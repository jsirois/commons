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

__author__ = 'John Sirois'

from twitter.pants.tasks import Task

from twitter.pants.base import BuildFile, Target
from twitter.pants import get_buildroot

class Filemap(Task):
  """Outputs a mapping from source file to the target that owns the source file."""

  __command__ = 'filemap'

  def __init__(self, context):
    Task.__init__(self, context)

  def execute(self, expanded_target_addresses):
    if (len(self.context.target_roots) > 0):
      for target in self.context.target_roots:
        self._execute_target(target)
    else:
      root_dir = get_buildroot()
      for buildfile in BuildFile.scan_buildfiles(root_dir):
        target_addresses = Target.get_all_addresses(buildfile)
        for target_address in target_addresses:
          target = Target.get(target_address)
          self._execute_target(target)

  def _execute_target(self, target):
    if hasattr(target, 'sources') and target.sources is not None:
      for sourcefile in target.sources:
        print(sourcefile, target.address)
