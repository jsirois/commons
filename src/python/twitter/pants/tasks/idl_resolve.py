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

__author__ = 'Phil Hom'

import os

from twitter.pants import is_internal
from twitter.pants.tasks.ivy_resolve import IvyResolve


class IdlResolve(IvyResolve):

  # TODO(John Sirois): rework ivy_resolve to allow idl resolution without subclassing
  #   (via goal dependencies instead)
  def __init__(self, context):
    super(IdlResolve, self).__init__(context, ['idl'])

  def execute(self, targets):
    IvyResolve.execute(self, targets)
    self._populate_Idl_list()

  def _populate_Idl_list(self):
    with self._cachepath(self._classpath_file) as classpath:
      jars = {}
      for path in classpath:
        if self._is_idl(path):
          deps = []
          for target in self.context.targets(predicate=is_internal):
            for dep in target.dependencies:
              if os.path.basename(path).replace('-idl.jar','') in dep.id:
                deps.append(target)
          jars.update({path:deps})
      self.context.log.debug('Fetched idl jars: %s' % jars)
      self.context.products.idl_jars = jars

  def _is_idl(self, path):
    return path.endswith('-idl.jar')
