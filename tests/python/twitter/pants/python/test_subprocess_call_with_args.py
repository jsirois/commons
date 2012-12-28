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

import unittest
import errno

from twitter.pants.tasks.binary_utils import _subprocess_call, _subprocess_call_with_args

def make_dummy_path(dummy_str, maxfile, maxpath):
  dummy_file = ''
  for _ in range(0, maxfile/len(dummy_str)):
    dummy_file += dummy_str

  dummy_path = ''
  for _ in range(0, maxpath/maxfile):
    dummy_path += "/" + dummy_file

  return dummy_path

def make_dummy_arg_list(dummy_path, maxargs):
  arg_list = []
  for _ in range(0, maxargs/len(dummy_path)):
    arg_list.append(dummy_path)
  return arg_list

class SubprocessCallWithArgs(unittest.TestCase):

  def test_subprocess_call_with_args(self):
    cmd = ["/usr/bin/true"] # always returns 0 and ignores command line opts/args
    
    dummy_str = '0123456789abcdef'
    maxfile = 256/4
    maxpath = 1024/2
    maxargs = 256 * 1024
    args = make_dummy_arg_list(make_dummy_path(dummy_str, maxfile, maxpath), maxargs * 2)
    cmd_with_args = cmd[:]
    cmd_with_args.extend(args)

    xfail = False
    try:
      _subprocess_call(cmd_with_args) # this should fail
    except OSError as err:
      if err.errno == errno.E2BIG:
        xfail = True
    self.assertTrue(xfail)

    success = True
    try:
      _subprocess_call_with_args(cmd, args) # this should succeed
    except OSError as err:
      success = False
    self.assertTrue(success)
