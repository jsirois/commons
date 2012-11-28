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

import os
import subprocess
import sys

from collections import defaultdict

from twitter.pants import get_buildroot, has_sources
from twitter.pants.base.build_file import BuildFile
from twitter.pants.base.target import Target
from twitter.pants.tasks import TaskError
from twitter.pants.tasks.console_task import ConsoleTask


class WhatChanged(ConsoleTask):
  """Emits the targets that have been modified since a given commit."""

  @classmethod
  def setup_parser(cls, option_group, args, mkflag):
    super(WhatChanged, cls).setup_parser(option_group, args, mkflag)

    option_group.add_option(mkflag('parent'), dest='what_changed_create_prefix', default='HEAD',
                            help='[%default] Identifies the parent tree-ish to calculate changes '
                                 'against.')

    option_group.add_option(mkflag("files"), mkflag("files", negate=True), default=False,
                            action="callback", callback=mkflag.set_bool,
                            dest='what_changed_show_files',
                            help='[%default] Shows changed files instead of the targets that own '
                                 'them.')

  def __init__(self, context, outstream=sys.stdout, workspace=None):
    super(WhatChanged, self).__init__(context, outstream)

    self._parent = context.options.what_changed_create_prefix
    self._show_files = context.options.what_changed_show_files

    try:
      self._workspace = workspace or Workspace()
    except Workspace.WorkspaceError as e:
      raise TaskError('Failed to initialize workspace for change detection.', e)

    self._filemap = defaultdict(set)

  def console_output(self, _):
    touched_files = self._workspace.touched_files(self._parent)
    if self._show_files:
      for file in touched_files:
        yield file
    else:
      touched_targets = set()
      for file in touched_files:
        for touched_target in self._owning_targets(file):
          if touched_target not in touched_targets:
            touched_targets.add(touched_target)
            yield str(touched_target.address)

  def _owning_targets(self, file):
    for build_file in self._candidate_owners(file):
      is_build_file = (build_file.full_path == os.path.join(get_buildroot(), file))
      for address in Target.get_all_addresses(build_file):
        target = Target.get(address)
        if target and (is_build_file or (has_sources(target) and self._owns(target, file))):
          yield target

  def _candidate_owners(self, file):
    build_file = BuildFile(get_buildroot(), relpath=os.path.dirname(file), must_exist=False)
    if build_file.exists():
      yield build_file
    for sibling in build_file.siblings():
      yield sibling
    for ancestor in build_file.ancestors():
      yield ancestor

  def _owns(self, target, file):
    if target not in self._filemap:
      files = self._filemap[target]
      for owned_file in target.sources:
        owned_path = os.path.join(target.target_base, owned_file)
        files.add(owned_path)
    return file in self._filemap[target]


# TODO(John Sirois): plumb get_buildroot and buildinfo to interact with an SCM interface instead of
# relying upon git and use that interface here as well.

class Workspace(object):
  """Tracks the state of the current workspace."""

  class WorkspaceError(Exception):
    """Indicates a problem reading the local workspace."""

  def touched_files(self, parent):
    """Returns the set of paths modified between the given parent commit and the current local
    workspace state.
    """
    changes = ['git', 'diff', '--name-only', parent or 'HEAD']
    untracked = ['git', 'ls-files', '--other', '--exclude-standard']
    return self._collect_files(changes).union(self._collect_files(untracked))

  def _collect_files(self, cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = proc.communicate()
    if proc.returncode != 0:
      raise TaskError('Failed to determine changes: %s returned %d' % (cmd, proc.returncode))
    return set(stdout.split())

