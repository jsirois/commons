# ==================================================================================================
# Copyright 2011 Twitter, Inc.
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

import sys
import traceback

from twitter.pants.tasks import Task
from twitter.pants.tasks import TaskError

from twitter.pants import is_jvm, is_python
from twitter.pants.targets.jar_dependency import JarDependency


class Depmap(Task):
  """Generates either a textual dependency tree or a graphviz digraph dotfile for the dependency set
  of a target."""

  @classmethod
  def setup_parser(cls, option_group, args, mkflags):
    cls.internal_only_flag = mkflags("internal-only") # this should go away in a future refactoring
    cls.external_only_flag = mkflags("external-only") # this should go away in a future refactoring
    option_group.add_option(cls.internal_only_flag,
                            action="store_true",
                            dest="depmap_is_internal_only",
                            default=False,
                            help='Specifies that only internal dependencies should'
                                 ' be included in the graph output (no external jars).')
    option_group.add_option(cls.external_only_flag,
                            action="store_true",
                            dest="depmap_is_external_only",
                            default=False,
                            help='Specifies that only external dependencies should'
                                 ' be included in the graph output (only external jars).')
    option_group.add_option(mkflags("minimal"),
                            action="store_true",
                            dest="depmap_is_minimal",
                            default=False,
                            help='For a textual dependency tree, only prints a dependency the 1st'
                                 ' time it is encountered.  For graph output this does nothing.')
    option_group.add_option(mkflags("separator"),
                            dest="depmap_separator",
                            default="-",
                            help='Specifies the separator to use between the org/name/rev'
                                 ' components of a dependency\'s fully qualified name.')
    option_group.add_option(mkflags("graph"),
                            action="store_true",
                            dest="depmap_is_graph",
                            default=False,
                            help='Specifies the internal dependency graph should be'
                                 ' output in the dot digraph format')

  def __init__(self, context):
    Task.__init__(self, context)

    if (self.context.options.depmap_is_internal_only and
        self.context.options.depmap_is_external_only):
      cls = self.__class__
      error_str = "At most one of %s or %s can be selected." % ( cls.internal_only_flag,
                                                                 cls.external_only_flag )
      raise TaskError(error_str)

    self.is_internal_only = self.context.options.depmap_is_internal_only
    self.is_external_only = self.context.options.depmap_is_external_only
    self.is_minimal = self.context.options.depmap_is_minimal
    self.is_graph = self.context.options.depmap_is_graph
    self.separator = self.context.options.depmap_separator

  def execute(self, expanded_target_addresses):
    if len(self.context.target_roots) == 0:
      raise TaskError("One or more target addresses are required.")

    eol = ""
    for target in self.context.target_roots:
      print(end=eol)
      eol = "\n"
      if all(is_jvm(t) for t in target.resolve()):
        if self.is_graph:
          self._print_digraph(target)
        else:
          self._print_dependency_tree(target)
      elif is_python(target):
        if self.is_internal_only or self.is_external_only or self.is_minimal or self.is_graph:
          print('Unsupported option for Python target', file=sys.stderr)
          sys.exit(1)
          self._print_python_dependencies(target, 0)

  def _print_python_dependencies(self, target, indent):
    attrs = []
    print('%s%s%s %s' % (
        '*' if target.provides else '',
        ' ' * 4 * indent,
        target,
        '[provides: %s]' % target.provides.key if target.provides else ''
        ), file=sys.stderr, end='')
    if hasattr(target, 'sources') and target.sources and len(target.sources) > 0:
      attrs.append('sources: %d files' % len(target.sources))
    if hasattr(target, 'resources') and target.resources and len(target.resources) > 0:
      attrs.append('resources: %d files' % len(target.resources))
    if len(attrs) > 0:
      print('[%s]' % ', '.join(attrs))
      for src in target.sources:
        print('%ssrc: %s' % ((' ' * (4 * indent + 2), src)))
      for dat in target.resources:
        print('%sdat: %s' % ((' ' * (4 * indent + 2), dat)))
    else:
      print()
    if hasattr(target, 'dependencies'):
      for dep in target.dependencies:
        for d in dep.resolve():
          self._print_python_dependencies(d, indent + 1)

  def _dep_id(self, dependency):
    """Returns a tuple of dependency_id , is_internal_dep."""

    params = dict(sep=self.separator)
    if isinstance(dependency, JarDependency):
      params.update(dict(
        org=dependency.org,
        name=dependency.name,
        rev=dependency.rev,
      ))
    else:
      params.update(dict(
        org='internal',
        name=dependency.id,
      ))

    if params.get('rev'):
      return "%(org)s%(sep)s%(name)s%(sep)s%(rev)s" % params, False
    else:
      return "%(org)s%(sep)s%(name)s" % params, True

  def _print_dependency_tree(self, target):
    def print_dep(dep, indent):
      print("%s%s" % (indent * "  ", dep))

    def print_deps(printed, dep, indent=0):
      dep_id, _ = self._dep_id(dep)
      if dep_id in printed:
        if not self.is_minimal:
          print_dep("*%s" % dep_id, indent)
      else:
        if not self.is_external_only:
          print_dep(dep_id, indent)
          printed.add(dep_id)
          indent += 1

        if is_jvm(dep):
          for internal_dep in dep.internal_dependencies:
            print_deps(printed, internal_dep, indent)

        if not self.is_internal_only:
          if is_jvm(dep):
            for jar_dep in dep.jar_dependencies:
              jar_dep_id, internal = self._dep_id(jar_dep)
              if not internal:
                if jar_dep_id not in printed or (not self.is_minimal and not self.is_external_only):
                  print_dep(jar_dep_id, indent)
                  printed.add(jar_dep_id)

    printed = set()
    for t in target.resolve():
      print_deps(printed, t)

  def _print_digraph(self, target):
    def output_candidate(internal):
      return (self.is_internal_only and internal) or (
        self.is_external_only and not internal) or (
        not self.is_internal_only and not self.is_external_only)

    def print_dep(dep):
      dep_id, internal = self._dep_id(dep)
      science_styled = internal and not self.is_internal_only
      twitter_styled = not internal and dep.org.startswith('com.twitter')

      if science_styled:
        fmt = '  "%(id)s" [label="%(id)s", style="filled", fillcolor="#0084b4", fontcolor="white"];'
        print(fmt % { 'id': dep_id })
      elif twitter_styled:
        print('  "%s" [style="filled", fillcolor="#c0deed"];' % dep_id)
      else:
        print('  "%s";' % dep_id)

    def print_deps(printed, dep):
      if dep not in printed:
        printed.add(dep)

        for dependency in dep.resolve():
          if is_jvm(dependency):
            for internal_dependency in dependency.internal_dependencies:
              print_deps(printed, internal_dependency)

          for jar in (dependency.jar_dependencies if is_jvm(dependency) else [dependency]):
            jar_id, internal = self._dep_id(jar)
            if output_candidate(internal):
              if jar not in printed:
                print_dep(jar)
                printed.add(jar)

              target_id, _ = self._dep_id(target)
              dep_id, _ = self._dep_id(dependency)
              left_id = target_id if self.is_external_only else dep_id
              if (left_id, jar_id) not in printed:
                styled = internal and not self.is_internal_only
                print('  "%s" -> "%s"%s;' % (left_id, jar_id, ' [style="dashed"]' if styled else ''))
                printed.add((left_id, jar_id))

    print('digraph "%s" {' % target.id)
    print_dep(target)
    print_deps(set(), target)
    print('}')
