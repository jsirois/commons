# ==================================================================================================
# Copyright 2012 Twitter, Inc.
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

from __future__ import print_function

import os
import sys
import re
import subprocess
import tempfile

from collections import defaultdict

from twitter.common import log
from twitter.common.collections import OrderedSet
from twitter.common.dirutil import safe_mkdir

from twitter.pants import is_jvm
from twitter.pants.targets import (
  JavaLibrary,
  JavaThriftLibrary,
  ScalaLibrary)
from twitter.pants.tasks import TaskError
from twitter.pants.tasks.binary_utils import profile_classpath, runjava
from twitter.pants.tasks.code_gen import CodeGen
from twitter.pants.thrift_util import calculate_compile_sources

SCROOGE_MAIN = 'com.twitter.scrooge.Main'

class ScroogeGen(CodeGen):
  class GenInfo(object):
    def __init__(self, gen, deps):
      self.gen = gen
      self.deps = deps

  @classmethod
  def setup_parser(cls, option_group, args, mkflag):
    option_group.add_option(mkflag("outdir"), dest="scrooge_gen_create_outdir",
                            help="Emit generated code in to this directory.")

    option_group.add_option(mkflag("lang"), dest="scrooge_gen_langs",  default=[],
                            action="append", type="choice", choices=['scala', 'java'],
                            help="Force generation of thrift code for these languages.  Both "
                                 "'scala' and 'java' are supported")

  def __init__(self, context):
    CodeGen.__init__(self, context)

    self.classpath = profile_classpath('scrooge-gen')
    self.output_dir = (
      context.options.scrooge_gen_create_outdir
      or context.config.get('scrooge-gen', 'workdir')
    )
    self.output_dir = os.path.relpath(self.output_dir)
    self.strict  = context.config.getbool('scrooge-gen', 'strict')
    self.verbose = context.config.getbool('scrooge-gen', 'verbose')


    def create_geninfo(key):
      gen_info = context.config.getdict('scrooge-gen', key)
      gen = gen_info['gen']
      deps = {}
      for category, depspecs in gen_info['deps'].items():
        dependencies = OrderedSet()
        deps[category] = dependencies
        for depspec in depspecs:
          dependencies.update(context.resolve(depspec))
      return ScroogeGen.GenInfo(gen, deps)

    self.gen_java = create_geninfo('java')
    self.gen_scala = create_geninfo('scala')

    self.gen_langs = set(context.options.scrooge_gen_langs)
    if len(self.gen_langs) > 1:
      raise TaskError('Multiple Scrooge generation languages not currently supported.')

    for lang in ('java', 'scala'):
      if self.context.products.isrequired(lang):
        self.gen_langs.add(lang)


  def invalidate_for(self):
    return self.gen_langs

  def is_gentarget(self, target):
    return isinstance(target, JavaThriftLibrary) and 'scrooge' == target.compiler

  def is_forced(self, lang):
    return lang in self.gen_langs

  def genlangs(self):
    return dict(java=is_jvm, scala=is_jvm)

  def genlang(self, lang, targets):
    bases, sources = calculate_compile_sources(targets, self.is_gentarget)

    safe_mkdir(self.output_dir)
    try:
      gen_file_map = mkstempname()

      args = [
        '--language', lang,
        '--dest', self.output_dir,
        '--gen-file-map', gen_file_map,
        '--finagle',
        '--ostrich',
        ]

      if not self.strict:
        args.append('--disable-strict')
      if self.verbose:
          args.append('--verbose')

      for base in bases:
        args.extend(('--import-path', base))

      args.extend(sources)

      if 0 != runjava(main=SCROOGE_MAIN, classpath=self.classpath, args=args):
        raise TaskError

      self.gen_files_by_source = self.parse_gen_file_map(gen_file_map)
    finally:
      if os.path.exists(gen_file_map):
        os.remove(gen_file_map)

  def createtarget(self, lang, gentarget, dependees):
    if lang == 'java':
      return self._create_java_target(gentarget, dependees)
    elif lang == 'scala':
      return self._create_scala_target(gentarget, dependees)
    else:
      raise TaskError('Unrecognized scrooge gen lang: %s' % lang)

  # TODO(Robert Nielsen): merge these two into one (maybe move to _inject_target()
  def _create_java_target(self, target, dependees):
    def create_target(files, deps):
       return self.context.add_new_target(self.output_dir,
                                          JavaLibrary,
                                          name=target.id,
                                          provides=target.provides,
                                          sources=files,
                                          dependencies=deps)
    return self._inject_target(target, dependees, self.gen_java, 'java', create_target)

  def _create_scala_target(self, target, dependees):
    def create_target(files, deps):
     return self.context.add_new_target(self.output_dir,
                                        ScalaLibrary,
                                        name=target.id,
                                        provides=target.provides,
                                        sources=files,
                                        dependencies=deps)
    return self._inject_target(target, dependees, self.gen_scala, 'scala', create_target)

  def _inject_target(self, target, dependees, geninfo, namespace, create_target):
    files = []
    has_service = False
    for source in target.sources:
      services, genfiles = calculate_gen(os.path.join(target.target_base, source), self.gen_files_by_source)
      has_service = has_service or services
      files.extend(genfiles.get(namespace, []))
    deps = geninfo.deps['service' if has_service else 'structs']
    tgt = create_target(files, deps)
    tgt.id = target.id
    tgt.is_codegen = True
    for dependee in dependees:
      dependee.update_dependencies([tgt])
    return tgt

  def parse_gen_file_map(self, gen_file_map):
    d = dict()
    with open(gen_file_map, 'r') as deps:
      for dep in deps.readlines():
        src, cls = dep.strip().split('->')
        src = os.path.relpath(src.strip(), os.path.curdir)
        cls = os.path.relpath(cls.strip(), self.output_dir)

        if src not in d:
          d[src] = set([])
        d[src].add(cls)
    return d

NAMESPACE_PARSER = re.compile(r'^\s*namespace\s+([^\s]+)\s+([^\s]+)\s*$')
TYPE_PARSER = re.compile(r'^\s*(const|enum|exception|service|struct|union)\s+([^\s{]+).*')


# TODO(John Sirois): consolidate thrift parsing to 1 pass instead of 2
def calculate_gen(source, gen_files_by_source):
  """Calculates the service types and files generated for the given thrift IDL source.

  Returns a tuple of (service types, generated files).
  """

  with open(source, 'r') as thrift:
    lines = thrift.readlines()
    namespaces = {}
    types = defaultdict(set)
    for line in lines:
      match = NAMESPACE_PARSER.match(line)
      if match:
        lang = match.group(1)
        namespace = match.group(2)
        namespaces[lang] = namespace
      else:
        match = TYPE_PARSER.match(line)
        if match:
          typename = match.group(1)
          name = match.group(2)
          types[typename].add(name)

    gen_files_by_lang = defaultdict(set)

    gen_files_by_lang['scala'].update(filter_gen_files(source, gen_files_by_source, '.scala'))
    gen_files_by_lang['java'].update(filter_gen_files(source, gen_files_by_source, '.java'))

    return types['service'], gen_files_by_lang


def filter_gen_files(source, gen_files_by_source, ext):
  for gen_file in gen_files_by_source[source]:
    if gen_file.endswith(ext):
      yield gen_file


def mkstempname():
  try:
    handle, name = tempfile.mkstemp()
    os.close(handle)
  except IOError as e:
    raise TaskError('IOError: errno=%i: "%s"' % (e.errno, e.strerror), file=sys.stderr)
  return name
