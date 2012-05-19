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

__author__ = 'Brian Larson'

import os
from twitter.common.collections import OrderedSet
from twitter.common.dirutil import safe_mkdir

from twitter.pants import get_buildroot, is_jvm
from twitter.pants.targets import JavaLibrary, JavaAntlrLibrary
from twitter.pants.tasks import binary_utils, Task, TaskError
from twitter.pants.tasks.binary_utils import nailgun_profile_classpath, safe_args
from twitter.pants.tasks.code_gen import CodeGen
from twitter.pants.tasks.nailgun_task import NailgunTask

CONFIG_KEY = 'antlr-gen'

class AntlrGen(CodeGen, NailgunTask):

  def __init__(self, context):
    CodeGen.__init__(self, context)
    NailgunTask.__init__(self, context)

    def resolve_deps(key):
      deps = OrderedSet()
      for dep in context.config.getlist(CONFIG_KEY, 'javadeps'):
        deps.update(context.resolve(dep))
      return deps

    self.antlr_profile = context.config.get(CONFIG_KEY, 'antlr_profile')
    self.java_out = os.path.join(context.config.get(CONFIG_KEY, 'workdir'), 'gen-java')
    self.javadeps = resolve_deps('javadeps')

  def is_gentarget(self, target):
    return isinstance(target, JavaAntlrLibrary)

  def is_forced(self, lang):
    return True

  def genlangs(self):
    return dict(java=is_jvm)

  def genlang(self, lang, targets):
    if lang != 'java':
      raise TaskError('Unrecognized antlr gen lang: %s' % lang)
    sources = self._calculate_sources(targets)
    safe_mkdir(self.java_out)

    antlr_classpath = nailgun_profile_classpath(self, self.antlr_profile)
    antlr_args = ["-o", self.java_out ]
    for source in sources:
      antlr_args.append(source)

    self.runjava("org.antlr.Tool", classpath=antlr_classpath, args=antlr_args)

  def _calculate_sources(self, targets):
    sources = set()
    def collect_sources(target):
      if self.is_gentarget(target):
        sources.update(os.path.join(target.target_base, source) for source in target.sources)
    for target in targets:
      target.walk(collect_sources)
    return sources

  def createtarget(self, lang, gentarget, dependees):
    if lang != 'java':
      raise TaskError('Unrecognized antlr gen lang: %s' % lang)
    return self._create_java_target(gentarget, dependees)

  def _create_java_target(self, target, dependees):
    generated_sources = []
    for source in target.sources:
      # Antlr enforces that generated sources are relative to the base filename, and that
      # each grammar filename must match the resulting grammar Lexer and Parser classes.
      source_base, source_ext = os.path.splitext(source)
      generated_sources.append(os.path.join(target.target_base, source_base + "Lexer.java"))
      generated_sources.append(os.path.join(target.target_base, source_base + "Parser.java"))

    tgt = self.context.add_new_target(self.java_out,
                                      JavaLibrary,
                                      name=target.id,
                                      provides=target.provides,
                                      sources=generated_sources,
                                      dependencies=self.javadeps)
    tgt.id = target.id
    tgt.is_codegen = True
    for dependee in dependees:
      dependee.update_dependencies([tgt])
    return tgt
