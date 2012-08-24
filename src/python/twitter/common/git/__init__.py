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

import contextlib
from twitter.common.lang import Compatibility

import git


class DirtyRepositoryError(Exception):
  def __init__(self, branch=None):
    super(DirtyRepositoryError, self).__init__('%s must not be dirty!' % (
      'Current branch (%s)' % branch if branch else 'Current branch'))


@contextlib.contextmanager
def branch(sha, project=None):
  """
    Perform actions at a given sha in a repository.  Implemented as a context manager.
    Must be run in the CWD of a git repository.

    sha: A fully-qualified revision as specified in:
      http://www.kernel.org/pub/software/scm/git/docs/git-rev-parse.html

    project (optional): A label to prepend to the temporary branch.

    Example:
      import subprocess
      from twitter.common.git import branch
      with branch('master@{yesterday}'):
        subprocess.check_call('./pants tests/python/twitter/common:all')
  """

  repo = git.Repo()
  active_head = repo.active_branch

  if repo.is_dirty():
    raise DirtyRepositoryError(active_head)
  else:
    print('Active head: %s' % active_head)

  branch_name = '_%s_' % sha
  if project:
    assert isinstance(project, Compatibility.string)
    branch_name = '_' + project + branch_name

  try:
    print('Creating head %s' % branch_name)
    head = repo.create_head(branch_name)
    head.commit = sha
    head.checkout()
    yield
  except Exception as e:
    print('Caught exception: %s' % e)
  finally:
    print('Resetting head: %s' % active_head)
    active_head.checkout()
    print('Deleting temporary head: %s' % branch_name)
    repo.delete_head(branch_name, force=True)
