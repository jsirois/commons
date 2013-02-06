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

from twitter.pants.targets.exportable_jvm_library import ExportableJvmLibrary


class JavaThriftLibrary(ExportableJvmLibrary):
  """Defines a target that builds java or scala stubs from a thrift IDL file."""

  def __init__(self,
               name,
               sources,
               provides = None,
               dependencies = None,
               excludes = None,
               compiler = None,
               language = None,
               namespace_map = None,
               buildflags = None):

    """name: The name of this module target, addressable via pants via the portion of the spec
        following the colon
    sources: A list of paths containing the thrift source files this module's jar is compiled from
    provides: An optional Dependency object indicating the The ivy artifact to export
    dependencies: An optional list of Dependency objects specifying the binary (jar) dependencies of
        this module.
    excludes: An optional list of dependency exclude patterns to filter all of this module's
        transitive dependencies against.
    compiler: An optional compiler used to compile the thrift files.
    language: The language used to generate the output files.
    namespace_map: A dictionary of namespaces to remap (old: new)
    buildflags: A list of additional command line arguments to pass to the underlying build system
        for this target"""

    ExportableJvmLibrary.__init__(self,
                                  name,
                                  sources,
                                  provides,
                                  dependencies,
                                  excludes,
                                  buildflags)
    self.add_label('java')
    self.add_label('codegen')

    # TODO(John Sirois): the default compiler should be grabbed from the workspace config
    self.compiler = compiler or 'thrift'

    self.language = language
    self.namespace_map = namespace_map

  def _as_jar_dependency(self):
    return ExportableJvmLibrary._as_jar_dependency(self).with_sources()
