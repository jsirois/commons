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
import errno
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
from twitter.pants.tasks.binary_utils import profile_classpath, runjava_indivisible
from twitter.pants.tasks.code_gen import CodeGen
from twitter.pants.thrift_util import calculate_compile_sources

INFO_FOR_COMPILER = { 'scrooge':   { 'config': 'scrooge-gen',
                                     'main':   'com.twitter.scrooge.Main',
                                     'langs':  frozenset(['scala', 'java']) },

                      'scrooge-2': { 'config': 'scrooge-2-gen',
                                     'main':   'com.twitter.scrooge.Main',
                                     'langs':  frozenset(['scala']) } }

INFO_FOR_LANG = { 'java':   { 'target_type': JavaLibrary,
                              'ext':         'java',
                              'predicate':   is_jvm },

                  'scala':  { 'target_type': ScalaLibrary,
                              'ext':         'scala',
                              'predicate':   is_jvm } }

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
                            action="append", type="choice", choices=INFO_FOR_LANG.keys(),
                            help="Force generation of thrift code for these languages.  Both "
                                 "'scala' and 'java' are supported")

  def __init__(self, context):
    CodeGen.__init__(self, context)

    self.gen_langs = set(context.options.scrooge_gen_langs)
    self.compilers = dict()

    for compiler in targets_for_compiler(context.targets(is_gentarget)):
      compiler_info = self.compilers[compiler] = dict()
      compiler_config = INFO_FOR_COMPILER[compiler]['config']
      compiler_info['classpath'] = profile_classpath(compiler_config)
      compiler_info['outdir'] = (
        context.options.scrooge_gen_create_outdir
        or context.config.get(compiler_config, 'workdir')
        )
      compiler_info['outdir'] = os.path.relpath(compiler_info['outdir'])
      compiler_info['strict']  = context.config.getbool(compiler_config, 'strict')
      compiler_info['verbose'] = context.config.getbool(compiler_config, 'verbose')

      def create_geninfo(key):
        gen_info = context.config.getdict(compiler_config, key)
        gen = gen_info['gen']
        deps = dict()
        for category, depspecs in gen_info['deps'].items():
          dependencies = OrderedSet()
          deps[category] = dependencies
          for depspec in depspecs:
            dependencies.update(context.resolve(depspec))
        return self.GenInfo(gen, deps)

      compiler_info['gen'] = dict()

      for lang in INFO_FOR_COMPILER[compiler]['langs']:
        compiler_info['gen'][lang] = create_geninfo(lang)
        if self.context.products.isrequired(lang):
          self.gen_langs.add(lang)

  def invalidate_for(self):
    return self.gen_langs

  def is_gentarget(self, target):
    return is_gentarget(target)

  def is_forced(self, lang):
    return lang in self.gen_langs

  def genlangs(self):
    result = dict()
    for lang in INFO_FOR_LANG:
      result[lang] = INFO_FOR_LANG[lang]['predicate']
    return result

  def genlang(self, lang, targets):
    compiler_targets = targets_for_compiler(targets)
    for compiler, targets in compiler_targets.items():
      bases, sources = calculate_compile_sources(targets, self.is_gentarget)
      compiler_info = self.compilers[compiler]

      safe_mkdir(compiler_info['outdir'])
      try:
        gen_file_map = mkstempname()

        opts = [
          '--language', lang,
          '--dest', compiler_info['outdir'],
          '--gen-file-map', gen_file_map,
          # TODO(Robert Nielsen): we need both of the following configurable in the BUILD file
          '--finagle',
          '--ostrich',
          ]

        # TODO(Robert Nielsen): we need --namespace-map configurable in the BUILD file

        if not compiler_info['strict']:
          opts.append('--disable-strict')
        if compiler_info['verbose']:
          opts.append('--verbose')

        for base in bases:
          opts.extend(('--import-path', base))

        if 0 != runjava_indivisible(main=INFO_FOR_COMPILER[compiler]['main'],
                                    classpath=compiler_info['classpath'], opts=opts, args=sources):
          raise TaskError

        compiler_info['gen_files_for_source'] = self.parse_gen_file_map(gen_file_map,
                                                                        compiler_info['outdir'])
      finally:
        if os.path.exists(gen_file_map):
          os.remove(gen_file_map)

  def createtarget(self, lang, gentarget, dependees):
    if lang not in INFO_FOR_LANG:
      raise TaskError('Unrecognized scrooge gen lang: %s' % lang)
    def create_target(files, deps):
       return self.context.add_new_target(self.compilers[gentarget.compiler]['outdir'],
                                          INFO_FOR_LANG[lang]['target_type'],
                                          name=gentarget.id,
                                          provides=gentarget.provides,
                                          sources=files,
                                          dependencies=deps)
    return self._inject_target(gentarget, dependees, self.compilers[gentarget.compiler]['gen'][lang],
                               lang, create_target)

  def _inject_target(self, target, dependees, geninfo, namespace, create_target):
    files = []
    has_service = False
    for source in target.sources:
      services, genfiles = calculate_gen(os.path.join(target.target_base, source),
                                         self.compilers[target.compiler]['gen_files_for_source'])
      has_service = has_service or services
      files.extend(genfiles.get(namespace, []))
    deps = geninfo.deps['service' if has_service else 'structs']
    tgt = create_target(files, deps)
    tgt.id = target.id
    tgt.is_codegen = True
    for dependee in dependees:
      dependee.update_dependencies([tgt])
    return tgt

  def parse_gen_file_map(self, gen_file_map, outdir):
    d = dict()
    with open(gen_file_map, 'r') as deps:
      for dep in deps.readlines():
        src, cls = dep.strip().split('->')
        src = os.path.relpath(src.strip(), os.path.curdir)
        cls = os.path.relpath(cls.strip(), outdir)

        if src not in d:
          d[src] = set()
        d[src].add(cls)
    return d

NAMESPACE_PARSER = re.compile(r'^\s*namespace\s+([^\s]+)\s+([^\s]+)\s*$')
TYPE_PARSER = re.compile(r'^\s*(const|enum|exception|service|struct|union)\s+([^\s{]+).*')


# TODO(John Sirois): consolidate thrift parsing to 1 pass instead of 2
def calculate_gen(source, gen_files_for_source):
  """Calculates the service types and files generated for the given thrift IDL source.

  Returns a tuple of (service types, generated files).
  """

  with open(source, 'r') as thrift:
    lines = thrift.readlines()
    namespaces = dict()
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

    for lang in INFO_FOR_LANG:
      gen_files_by_lang[lang].update(filter_gen_files(source, gen_files_for_source,
                                                      INFO_FOR_LANG[lang]['ext']))

    return types['service'], gen_files_by_lang


def is_gentarget(target):
  return isinstance(target, JavaThriftLibrary) and INFO_FOR_COMPILER.get(target.compiler)


def targets_for_compiler(targets):
  result = defaultdict(set)
  for target in targets:
    result[target.compiler].add(target)
  return result


def filter_gen_files(source, gen_files_for_source, ext):
  for gen_file in gen_files_for_source[source]:
    if gen_file.endswith('.' + ext):
      yield gen_file


def mkstempname():
  try:
    handle, name = tempfile.mkstemp()
    os.close(handle)
  except OSError as e:
    raise TaskError('OSError: errno=%s: "%s"' % (errno.errorcode(e.errno), e.strerror), file=sys.stderr)
  return name
