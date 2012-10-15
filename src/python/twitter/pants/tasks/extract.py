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

__author__ = 'Phil Hom'

import os

from collections import defaultdict

from twitter.common import log
from twitter.common.collections import OrderedSet
from twitter.common.contextutil import open_zip

from twitter.pants.targets import JavaThriftLibrary
from twitter.pants.tasks import TaskError, Task
from twitter.pants.base.fileset import Fileset
from twitter.pants.tasks.binary_utils import safe_extract

class Extract(Task):

  def __init__(self, context):
    Task.__init__(self, context)
    self._target_dir = context.config.getdefault('pants_workdir')

  def execute(self, targets):
    # TODO(John Sirois): actually .add(...) these to the context
    jars = self.context.products.idl_jars
    for jar in jars.keys():
      sources = self._extract(jar)
      name = os.path.basename(jar)
      tgt = self._create_java_thrift_target(os.path.basename(jar), sources)
      for target in jars[jar]:
        target.dependencies.add(tgt)

  def _extract(self, jar):
    self.context.log.debug('Extracting idl jar to: %s' % self._target_dir)
    safe_extract(jar, self._target_dir)
    contents = self._list_jar_content(jar)
    sources = []
    for content in contents:
      if content.endswith('.thrift'):
        sources.append(os.path.join(self._target_dir, content))
    return sources

  def _create_java_thrift_target(self, name, files, deps=None):
    return self.context.add_new_target('.',
                                       JavaThriftLibrary,
                                       name=name,
                                       sources=files,
                                       dependencies=deps)

  def _list_jar_content(self, path):
    contents = []
    with open_zip(path) as zip:
      for path in zip.namelist():
        contents.append(path)
    return contents