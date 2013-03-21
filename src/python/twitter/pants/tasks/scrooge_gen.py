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
import re

from collections import defaultdict

from twitter.common.collections import OrderedSet
from twitter.common.contextutil import temporary_file
from twitter.common.dirutil import safe_mkdir

from twitter.pants import get_buildroot
from twitter.pants.binary_util import profile_classpath, runjava_indivisible
from twitter.pants.targets import (
  JavaLibrary,
  JavaThriftLibrary,
  ScalaLibrary)
from twitter.pants.tasks import TaskError
from twitter.pants.tasks.nailgun_task import NailgunTask
from twitter.pants.thrift_util import calculate_compile_sources

INFO_FOR_COMPILER = { 'scrooge':        { 'config': 'scrooge-gen',
                                          'main':   'com.twitter.scrooge.Main',
                                          'langs':  frozenset(['scala', 'java']) },

                      'scrooge-legacy': { 'config': 'scrooge-legacy-gen',
                                          'main':   'com.twitter.scrooge.Main',
                                          'langs':  frozenset(['scala']) } }

INFO_FOR_LANG = { 'scala':  { 'target_type': ScalaLibrary },
                  'java':   { 'target_type': JavaLibrary  } }


class ScroogeGen(NailgunTask):
  class GenInfo(object):
    def __init__(self, gen, deps):
      self.gen = gen
      self.deps = deps

  @classmethod
  def setup_parser(cls, option_group, args, mkflag):
    option_group.add_option(mkflag("outdir"), dest="scrooge_gen_create_outdir",
                            help="Emit generated code in to this directory.")

  def __init__(self, context):
    NailgunTask.__init__(self, context)

    self.compilers = defaultdict(lambda: defaultdict(dict))

    for compiler,lang2targets in compiler_to_lang_to_tgts(context.targets(is_gentarget)).items():
      for lang, targets in lang2targets.items():
        compiler_config = INFO_FOR_COMPILER[compiler]['config']
        compiler_lang_info = self.compilers[compiler][lang]
        compiler_lang_info['classpath'] = profile_classpath(compiler_config)
        compiler_lang_info['outdir'] = (
          context.options.scrooge_gen_create_outdir
          or context.config.get(compiler_config, 'workdir')
          )
        compiler_lang_info['outdir'] = os.path.relpath(compiler_lang_info['outdir'])
        compiler_lang_info['strict']  = context.config.getbool(compiler_config, 'strict')
        compiler_lang_info['verbose'] = context.config.getbool(compiler_config, 'verbose')

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

        compiler_lang_info['gen'] = create_geninfo(lang)

  def execute(self, targets):
    gentargets_by_dependee = self.context.dependants(
      on_predicate=is_gentarget,
      from_predicate=lambda t: not is_gentarget(t)
    )
    dependees_by_gentarget = defaultdict(set)
    for dependee, tgts in gentargets_by_dependee.items():
      for gentarget in tgts:
        dependees_by_gentarget[gentarget].add(dependee)

    # TODO(Robert Nielsen): Add optimization to only regenerate the files that have changed
    # initially we could just cache the generated file names and make subsequent invocations faster
    # but a feature like --dry-run will likely be added to scrooge to get these file names (without
    # actually doing the work of generating)
    # AWESOME-1563

    for compiler, lang_to_tgts in compiler_to_lang_to_tgts(filter(is_gentarget, targets)).items():
      for lang, compiler_lang_targets in lang_to_tgts.items():
        bases, sources = calculate_compile_sources(compiler_lang_targets, is_gentarget)
        compiler_lang_info = self.compilers[compiler][lang]
        opts = []

        if not compiler_lang_info['strict']:
          opts.append('--disable-strict')
        if compiler_lang_info['verbose']:
          opts.append('--verbose')

        # TODO(Robert Nielsen): we need both of the following configurable in the BUILD file
        opts.append('--finagle')
        opts.append('--ostrich')

        safe_mkdir(compiler_lang_info['outdir'])
        opts.extend(('--language', lang,
                     '--dest', compiler_lang_info['outdir']))

        for base in bases:
          opts.extend(('--import-path', base))

        for lhs, rhs in namespace_map(compiler_lang_targets).items():
          opts.extend(('--namespace-map', '%s=%s' % (lhs, rhs)))

        with temporary_file() as gen_file_map:
          gen_file_map.close()
          opts.extend(('--gen-file-map', gen_file_map.name))

          returncode = runjava_indivisible(main=INFO_FOR_COMPILER[compiler]['main'],
                                           classpath=compiler_lang_info['classpath'],
                                           opts=opts, args=sources)
          if 0 != returncode:
            raise TaskError("java %s ... exited non-zero (%i)" % \
                              (INFO_FOR_COMPILER[compiler]['main'], returncode))

          gen_files_for_source = self.parse_gen_file_map(gen_file_map.name,
                                                         compiler_lang_info['outdir'])

        langtarget_by_gentarget = {}
        for target in compiler_lang_targets:
          dependees = dependees_by_gentarget.get(target, [])
          langtarget_by_gentarget[target] = self.createtarget(target, dependees,
                                                              gen_files_for_source)

        genmap = self.context.products.get(lang)
        # synmap is a reverse map
        # such as a map of java library target generated from java thrift target
        synmap = self.context.products.get(lang + ':rev')
        for gentarget, langtarget in langtarget_by_gentarget.items():
          synmap.add(langtarget, get_buildroot(), [gentarget])
          genmap.add(gentarget, get_buildroot(), [langtarget])
          for dep in gentarget.internal_dependencies:
            if is_gentarget(dep):
              langtarget.update_dependencies([langtarget_by_gentarget[dep]])

  def createtarget(self, gentarget, dependees, gen_files_for_source):
    assert is_gentarget(gentarget)

    def create_target(files, deps, outdir, target_type):
      return self.context.add_new_target(outdir,
                                         target_type,
                                         name=gentarget.id,
                                         provides=gentarget.provides,
                                         sources=files,
                                         dependencies=deps)
    compiler_lang_info = self.compilers[gentarget.compiler][gentarget.language]
    return self._inject_target(gentarget, dependees,
                               compiler_lang_info['gen'],
                               gen_files_for_source,
                               create_target)

  def _inject_target(self, target, dependees, geninfo, gen_files_for_source, create_target):
    files = []
    has_service = False
    for source_file in target.sources:
      source = os.path.join(target.target_base, source_file)
      services = calculate_services(source)
      genfiles = gen_files_for_source[source]
      has_service = has_service or services
      files.extend(genfiles)
    deps = OrderedSet(geninfo.deps['service' if has_service else 'structs'])
    deps.update(target.dependencies)
    compiler_lang_info = self.compilers[target.compiler][target.language]
    outdir = compiler_lang_info['outdir']
    target_type = INFO_FOR_LANG[target.language]['target_type']
    tgt = create_target(files, deps, outdir, target_type)
    tgt.id = target.id
    tgt.is_codegen = True
    for dependee in dependees:
      dependee.update_dependencies([tgt])
    return tgt

  def parse_gen_file_map(self, gen_file_map, outdir):
    d = defaultdict(set)
    with open(gen_file_map, 'r') as deps:
      for dep in deps:
        src, cls = dep.strip().split('->')
        src = os.path.relpath(src.strip(), os.path.curdir)
        cls = os.path.relpath(cls.strip(), outdir)
        d[src].add(cls)
    return d

NAMESPACE_PARSER = re.compile(r'^\s*namespace\s+([^\s]+)\s+([^\s]+)\s*$')
TYPE_PARSER = re.compile(r'^\s*(const|enum|exception|service|struct|union)\s+([^\s{]+).*')


# TODO(John Sirois): consolidate thrift parsing to 1 pass instead of 2
def calculate_services(source):
  """Calculates the services generated for the given thrift IDL source.
  Returns an interable of services
  """

  with open(source, 'r') as thrift:
    namespaces = dict()
    types = defaultdict(set)
    for line in thrift:
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

    return types['service']


def is_gentarget(target):
  result = (isinstance(target, JavaThriftLibrary)
            and hasattr(target, 'compiler')
            and hasattr(target, 'language')
            and target.compiler in INFO_FOR_COMPILER)

  if result and target.language not in INFO_FOR_COMPILER[target.compiler]['langs']:
    raise TaskError("%s can not generate %s" % (target.compiler, target.language))
  return result


def compiler_to_lang_to_tgts(targets):
  result = defaultdict(lambda: defaultdict(set))
  for target in targets:
    result[target.compiler][target.language].add(target)
  return result


def namespace_map(targets):
  result = dict()
  target_for_lhs = dict()
  for target in targets:
    if target.namespace_map:
      for lhs, rhs in target.namespace_map.items():
        current_rhs = result.get(lhs)
        if None == current_rhs:
          result[lhs] = rhs
          target_for_lhs[lhs] = target
        elif current_rhs != rhs:
          raise TaskError("Conflicting namespace_map values:\n\t%s {'%s': '%s'}\n\t%s {'%s': '%s'}"
                          % (target_for_lhs[lhs], lhs, current_rhs, target, lhs, rhs))
  return result
