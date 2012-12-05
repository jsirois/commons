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
import unittest

from twitter.common.contextutil import environment_as, pushd, temporary_dir
from twitter.common.dirutil import safe_open, safe_mkdtemp, safe_rmtree, touch

from twitter.pants.scm import Scm
from twitter.pants.scm.git import Git

class GitTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.origin = safe_mkdtemp()
    with pushd(cls.origin):
      subprocess.check_call(['git', 'init', '--bare'])

    cls.gitdir = safe_mkdtemp()
    cls.worktree = safe_mkdtemp()

    cls.readme_file = os.path.join(cls.worktree, 'README')

    with environment_as(GIT_DIR=cls.gitdir, GIT_WORK_TREE=cls.worktree):
      subprocess.check_call(['git', 'init'])
      subprocess.check_call(['git', 'remote', 'add', 'depot', cls.origin])

      touch(cls.readme_file)
      subprocess.check_call(['git', 'add', 'README'])
      subprocess.check_call(['git', 'commit', '-am', 'initial commit.'])
      subprocess.check_call(['git', 'tag', '-a', '-m', 'first tag', 'first'])
      subprocess.check_call(['git', 'push', '--tags', 'depot', 'master'])

      with safe_open(cls.readme_file, 'w') as readme:
        readme.write('Hello World.')
      subprocess.check_call(['git', 'commit', '-am', 'Update README.'])

    cls.clone2 = safe_mkdtemp()
    with pushd(cls.clone2):
      subprocess.check_call(['git', 'init'])
      subprocess.check_call(['git', 'remote', 'add', 'origin', cls.origin])
      subprocess.check_call(['git', 'pull', '--tags', 'origin', 'master:master'])

      with safe_open(os.path.realpath('README'), 'a') as readme:
        readme.write('--')
      subprocess.check_call(['git', 'commit', '-am', 'Update README 2.'])
      subprocess.check_call(['git', 'push', '--tags', 'origin', 'master'])

    cls.git = Git(gitdir=cls.gitdir, worktree=cls.worktree, remote='depot', branch='master')

  @classmethod
  def tearDownClass(cls):
    safe_rmtree(cls.origin)
    safe_rmtree(cls.gitdir)
    safe_rmtree(cls.worktree)
    safe_rmtree(cls.clone2)

  def test(self):
    self.assertEqual(set(), self.git.changed_files())
    self.assertEqual(set(['README']), self.git.changed_files(from_commit='HEAD^'))

    tip_sha = self.git.commit_id
    self.assertTrue(tip_sha)

    self.assertTrue(tip_sha in self.git.changelog())

    self.assertTrue(self.git.tag_name.startswith('first-'))
    self.assertEqual('master', self.git.branch_name)

    def edit_readme():
      with open(self.readme_file, 'a') as readme:
        readme.write('More data.')

    edit_readme()
    with open(os.path.join(self.worktree, 'INSTALL'), 'w') as untracked:
      untracked.write('make install')
    self.assertEqual(set(['README']), self.git.changed_files())
    self.assertEqual(set(['README', 'INSTALL']), self.git.changed_files(include_untracked=True))

    try:
      # These changes should be rejected because our branch point from origin is 1 commit behind
      # the changes pushed there in clone 2.
      self.git.commit('API Changes.')
    except Scm.RemoteException:
      with environment_as(GIT_DIR=self.gitdir, GIT_WORK_TREE=self.worktree):
        subprocess.check_call(['git', 'reset', '--hard', 'depot/master'])
      self.git.refresh()
      edit_readme()

    self.git.commit('''API '"' " Changes.''')
    self.git.tag('second', message='''Tagged ' " Changes''')

    with temporary_dir() as clone:
      with pushd(clone):
        subprocess.check_call(['git', 'init'])
        subprocess.check_call(['git', 'remote', 'add', 'origin', self.origin])
        subprocess.check_call(['git', 'pull', '--tags', 'origin', 'master:master'])

        with open(os.path.realpath('README')) as readme:
          self.assertEqual('--More data.', readme.read())

        git = Git()
        self.assertEqual('master', git.branch_name)
        self.assertEqual('second', git.tag_name)
