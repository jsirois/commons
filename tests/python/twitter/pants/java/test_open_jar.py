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
import unittest

from contextlib import contextmanager

from twitter.common.contextutil import temporary_dir, temporary_file
from twitter.common.dirutil import safe_mkdir

from twitter.pants.java import open_jar

class OpenJarTest(unittest.TestCase):

  @contextmanager
  def jarfile(self):
    with temporary_file() as fd:
      fd.close()
      yield fd.name

  def test_mkdirs(self):
    def assert_mkdirs(path, *entries):
      with self.jarfile() as jarfile:
        with open_jar(jarfile, 'w') as jar:
          jar.mkdirs(path)
        with open_jar(jarfile) as jar:
          self.assertEquals(list(entries), jar.namelist())

    assert_mkdirs('')
    assert_mkdirs('a', 'a/')
    assert_mkdirs('a/b/c', 'a/', 'a/b/', 'a/b/c/')

  def test_write_dir(self):
    with temporary_dir() as chroot:
      dir = os.path.join(chroot, 'a/b/c')
      safe_mkdir(dir)
      with self.jarfile() as jarfile:
        with open_jar(jarfile, 'w') as jar:
          jar.write(dir, 'd/e')
        with open_jar(jarfile) as jar:
          self.assertEquals(['d/', 'd/e/'], jar.namelist())

  def test_write_file(self):
    with temporary_dir() as chroot:
      dir = os.path.join(chroot, 'a/b/c')
      safe_mkdir(dir)
      data_file = os.path.join(dir, 'd.txt')
      with open(data_file, 'w') as fd:
        fd.write('e')
      with self.jarfile() as jarfile:
        with open_jar(jarfile, 'w') as jar:
          jar.write(data_file, 'f/g/h')
        with open_jar(jarfile) as jar:
          self.assertEquals(['f/', 'f/g/', 'f/g/h'], jar.namelist())
          self.assertEquals('e', jar.read('f/g/h'))

  def test_writestr(self):
    def assert_writestr(path, contents, *entries):
      with self.jarfile() as jarfile:
        with open_jar(jarfile, 'w') as jar:
          jar.writestr(path, contents)
        with open_jar(jarfile) as jar:
          self.assertEquals(list(entries), jar.namelist())
          self.assertEquals(contents, jar.read(path))

    assert_writestr('a.txt', 'b', 'a.txt')
    assert_writestr('a/b/c.txt', 'd', 'a/', 'a/b/', 'a/b/c.txt')
