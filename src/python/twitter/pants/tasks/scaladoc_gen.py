# ==================================================================================================
# Copyright 2013 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================

import os
import subprocess
import multiprocessing

from twitter.common.dirutil import safe_mkdir

from twitter.pants import binary_util, is_scala
from twitter.pants.tasks import Task, TaskError


class ScaladocGen(Task):
  @classmethod
  def setup_parser(cls, option_group, args, mkflag):
    option_group.add_option(mkflag("outdir"), dest="scaladoc_gen_outdir",
                            help="Emit scaladoc in this directory.")

    option_group.add_option(mkflag("transitive"), mkflag("transitive", negate=True),
                            dest="scaladoc_gen_transitive", default=True,
                            action="callback", callback=mkflag.set_bool,
                            help="[%default] Create scaladoc for the transitive closure of internal "
                                 "targets reachable from the roots specified on the command line.")

    combined_flag = mkflag("combined")
    option_group.add_option(combined_flag, mkflag("combined", negate=True),
                            dest="scaladoc_gen_combined", default=False,
                            action="callback", callback=mkflag.set_bool,
                            help="[%default] Generate scaladoc for all targets combined instead of "
                                 "each target individually.")

    option_group.add_option(mkflag("open"), mkflag("open", negate=True),
                            dest="scaladoc_gen_open", default=False,
                            action="callback", callback=mkflag.set_bool,
                            help="[%%default] Attempt to open the generated scaladoc in a browser "
                                 "(implies %s)." % combined_flag)

    option_group.add_option(mkflag("ignore-failure"), mkflag("ignore-failure", negate=True),
                            dest = "scaladoc_gen_ignore_failure", default=False,
                            action="callback", callback=mkflag.set_bool,
                            help="Specifies that scaladoc errors should not cause build errors")

  def __init__(self, context, output_dir=None, confs=None):
    Task.__init__(self, context)

    pants_workdir = context.config.getdefault('pants_workdir')
    self._output_dir = (
      output_dir
      or context.options.scaladoc_gen_outdir
      or context.config.get('scaladoc-gen',
                            'workdir',
                            default=os.path.join(pants_workdir, 'scaladoc'))
    )
    self.transitive = context.options.scaladoc_gen_transitive
    self.confs = confs or context.config.getlist('scaladoc-gen', 'confs', default=['default'])
    self.open = context.options.scaladoc_gen_open
    self.combined = self.open or context.options.scaladoc_gen_combined
    self.ignore_failure = context.options.scaladoc_gen_ignore_failure

  def invalidate_for(self):
    return self.combined

  def execute(self, targets):
    catalog = self.context.products.isrequired('scaladoc')
    if catalog and self.combined:
      raise TaskError('Cannot provide scaladoc target mappings for combined output')

    with self.changed(filter(is_scala, targets)) as changed_targets:
      safe_mkdir(self._output_dir)
      with self.context.state('classpath', []) as cp:
        classpath = [jar for conf, jar in cp if conf in self.confs]

        def find_scaladoc_targets():
          if self.transitive:
            return changed_targets
          else:
            return set(changed_targets).intersection(set(self.context.target_roots))

        scaladoc_targets = list(filter(is_scala, find_scaladoc_targets()))
        if self.combined:
          self.generate_combined(classpath, scaladoc_targets)
        else:
          self.generate_individual(classpath, scaladoc_targets)

    if catalog:
      for target in targets:
        gendir = self._gendir(target)
        scaladocs = []
        for root, dirs, files in os.walk(gendir):
          scaladocs.extend(os.path.relpath(os.path.join(root, f), gendir) for f in files)
        self.context.products.get('scaladoc').add(target, gendir, scaladocs)

  def generate_combined(self, classpath, targets):
    gendir = os.path.join(self._output_dir, 'combined')
    if targets:
      safe_mkdir(gendir, clean=True)
      command = create_scaladoc_command(classpath, gendir, *targets)
      if command:
        create_scaladoc(command, gendir)
    if self.open:
      binary_util.open(os.path.join(gendir, 'index.html'))

  def generate_individual(self, classpath, targets):
    jobs = {}
    for target in targets:
      gendir = self._gendir(target)
      command = create_scaladoc_command(classpath, gendir, target)
      if command:
        jobs[gendir] = (target, command)

    pool = multiprocessing.Pool(processes=min(len(jobs), multiprocessing.cpu_count()))
    try:
      # map would be a preferable api here but fails after the 1st batch with an internal:
      # ...
      #  File "...src/python/twitter/pants/tasks/jar_create.py", line 170, in javadocjar
      #      pool.map(createjar, jobs)
      #    File "...lib/python2.6/multiprocessing/pool.py", line 148, in map
      #      return self.map_async(func, iterable, chunksize).get()
      #    File "...lib/python2.6/multiprocessing/pool.py", line 422, in get
      #      raise self._value
      #  NameError: global name 'self' is not defined
      futures = []
      for gendir, (target, command) in jobs.items():
        futures.append(pool.apply_async(create_scaladoc, args=(command, gendir)))

      for future in futures:
        result, gendir = future.get()
        target, command = jobs[gendir]
        if result != 0:
          message = 'Failed to process scaladoc for %s [%d]: %s' % (target, result, command)
          if self.ignore_failure:
            self.context.log.warn(message)
          else:
            raise TaskError(message)

    finally:
      pool.close()

  def _gendir(self, target):
    return os.path.join(self._output_dir, target.id)


def create_scaladoc_command(classpath, gendir, *targets):
  sources = []
  for target in targets:
    sources.extend(os.path.join(target.target_base, source) for source in target.sources)

  if not sources:
    return None

  # TODO(John Chee): try scala.tools.nsc.ScalaDoc via ng
  command = [
    'scaladoc',
    '-usejavacp',
    '-classpath', ':'.join(classpath),
    '-d', gendir,
  ]

  command.extend(sources)
  return command


def create_scaladoc(command, gendir):
  safe_mkdir(gendir, clean=True)
  process = subprocess.Popen(command)
  result = process.wait()
  return result, gendir
