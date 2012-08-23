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

__author__ = 'Tejal Desai'

import os
import subprocess
from twitter.common import log
from twitter.common.contextutil import temporary_file


class CommandUtil:
  """
  This Class provides an wrapper to system command as a string and
  return the output.
  """
  @staticmethod
  def get_temp_filename():
    with temporary_file() as temp_file:
      tmp_filename = temp_file.name
      temp_file.close()
    return tmp_filename

  @staticmethod
  def _execute_internal(cmd, log_std_out, log_std_err, log_cmd, also_output_to_file=None, 
                        return_output=False):
    """
    Executes the command and returns 0 if successful
    Non-Zero status if command fails or an exception raised
    """
    tmp_filename = None
    if log_std_out or log_std_err:
      tmp_filename = CommandUtil.get_temp_filename()
      tmp_file = open(tmp_filename, "w")

    if (not log_std_err) or (not log_std_out):
      dev_null_file = open(os.devnull, "w")

    if log_std_out:
      if also_output_to_file:
        std_out_file = open(also_output_to_file, "w")
      else:
        std_out_file = tmp_file
    else:
      std_out_file = dev_null_file

    if log_std_err:
      std_err_file = tmp_file
    else:
      std_err_file = dev_null_file

    if log_cmd:
      log.info("Executing: %s" % " ".join(cmd))
    try:
      ret = subprocess.call(cmd, stdout=std_out_file, stderr=std_err_file)
    except OSError as exception:
      log.error("Exception occurred %s" % exception)
      return (1, None) if return_output else 1

    if tmp_filename:
      file_read = open(tmp_filename, "r")
      text = file_read.read()
      file_read.close()
      os.remove(tmp_filename)
      if text:
        log.info("External output:\n%s" % text)
        if return_output:
          return (ret, text)
    return ret

  @staticmethod
  def check_call(cmd):
    """
    Calls subprocess.check_call instead of subprocess.call
    """
    return subprocess.check_call(cmd)

  @staticmethod
  def execute(cmd, log_cmd=True, also_output_to_file=None):
    """
    Calls logs output and error if any
    """
    return CommandUtil._execute_internal(cmd, True, True, log_cmd, also_output_to_file)

  @staticmethod
  def execute_suppress_stdout(cmd, log_cmd=True):
    """
    Executes the command and supresses stdout
    """
    return CommandUtil._execute_internal(cmd, False, True, log_cmd)

  @staticmethod
  def execute_suppress_stdout_stderr(cmd, log_cmd=True):
    """
    Executes the command and supresses stdout and stderr
    """
    return CommandUtil._execute_internal(cmd, False, False, log_cmd)

  @staticmethod
  def execute_and_get_output(cmd, log_cmd=True):
    """
    Executes the command and returns the tuple return status and output
    If the subprocess.call raises an exception then returns error code and None as output
    If the command is in error returns the tuple return error code and error message
    return CommandUtil._execute_internal(cmd, True, True, log_cmd, None, True)
    """
    return CommandUtil._execute_internal(cmd, True, False, log_cmd, None, True)
