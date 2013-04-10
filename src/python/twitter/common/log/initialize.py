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

"""
Interface to Glog-stlye formatter.

import twitter.common.log

if not using twitter.common.app:
  for __main__:
    log = twitter.common.log.init('my_binary_name')
otherwise init will be called automatically on app.main()

for library/endpoint:
  from twitter.common import log

log.info('info baby')
log.debug('debug baby')
log.fatal('oops fatal!')

Will log to my_binary_name.{INFO,WARNING,ERROR,...} into log_dir using the
Google logging format.

See twitter.com.log.options for customizations.
"""

from __future__ import print_function

import os
import sys
import time
import logging
import getpass
from socket import gethostname

from twitter.common.log.formatters import glog, plain
from twitter.common.log.options import LogOptions
from twitter.common.dirutil import safe_mkdir


class GenericFilter(logging.Filter):
  def __init__(self, levelfn=lambda record_level: True):
    self._levelfn = levelfn
    logging.Filter.__init__(self)

  def filter(self, record):
    if self._levelfn(record.levelno):
      return 1
    return 0


class ProxyFormatter(logging.Formatter):
  class UnknownSchemeException(Exception): pass

  _SCHEME_TO_FORMATTER = {
    glog.GlogFormatter.SCHEME: glog.GlogFormatter(),
    plain.PlainFormatter.SCHEME: plain.PlainFormatter()
  }

  def __init__(self, scheme_fn):
    logging.Formatter.__init__(self)
    self._scheme_fn = scheme_fn

  def preamble(self):
    scheme = self._scheme_fn()
    if scheme not in ProxyFormatter._SCHEME_TO_FORMATTER:
      raise ProxyFormatter.UnknownSchemeException("Unknown logging scheme: %s" % scheme)
    formatter = ProxyFormatter._SCHEME_TO_FORMATTER[scheme]
    if hasattr(formatter, 'logfile_preamble') and callable(formatter.logfile_preamble):
      return formatter.logfile_preamble()

  def format(self, record):
    scheme = self._scheme_fn()
    if scheme not in ProxyFormatter._SCHEME_TO_FORMATTER:
      raise ProxyFormatter.UnknownSchemeException("Unknown logging scheme: %s" % scheme)
    return ProxyFormatter._SCHEME_TO_FORMATTER[scheme].format(record)


_FILTER_TYPES = {
  logging.DEBUG: 'DEBUG',
  logging.INFO: 'INFO',
  logging.WARN: 'WARNING',
  logging.ERROR: 'ERROR',
  logging.FATAL: 'FATAL' # strangely python logging transaltes this to CRITICAL
}


def _safe_setup_link(link_filename, real_filename):
  """
    Create a symlink from link_filename to real_filename.
  """
  real_filename = os.path.relpath(real_filename, os.path.dirname(link_filename))

  if os.path.exists(link_filename):
    try:
      os.unlink(link_filename)
    except OSError:
      pass
  try:
    os.symlink(real_filename, link_filename)
  except OSError as e:
    # Typically permission denied.
    pass


class PreambleFileHandler(logging.FileHandler):
  def __init__(self, filename, preamble=None):
    self._preamble = preamble
    logging.FileHandler.__init__(self, filename)

  def _open(self):
    stream = logging.FileHandler._open(self)
    if self._preamble:
      stream.write(self._preamble)
    return stream


def _setup_disk_logging(filebase):
  handlers = []
  logroot = LogOptions.log_dir()
  safe_mkdir(logroot)

  def gen_filter(level):
    return GenericFilter(
      lambda record_level: record_level == level and level >= LogOptions.disk_log_level())

  def gen_link_filename(filebase, level):
    return '%(filebase)s.%(level)s' % {
      'filebase': filebase,
      'level': level,
    }

  hostname = gethostname()
  username = getpass.getuser()
  pid = os.getpid()
  datestring = time.strftime('%Y%m%d-%H%M%S', time.localtime())

  def gen_verbose_filename(filebase, level):
    return '%(filebase)s.%(hostname)s.%(user)s.log.%(level)s.%(date)s.%(pid)s' % {
      'filebase': filebase,
      'hostname': hostname,
      'user': username,
      'level': level,
      'date': datestring,
      'pid': pid
    }

  for filter_type, filter_name in _FILTER_TYPES.items():
    formatter = ProxyFormatter(LogOptions.disk_log_scheme)
    filter = gen_filter(filter_type)
    full_filebase = os.path.join(logroot, filebase)
    logfile_link = gen_link_filename(full_filebase, filter_name)
    logfile_full = gen_verbose_filename(full_filebase, filter_name)
    file_handler = PreambleFileHandler(logfile_full, formatter.preamble())
    file_handler.setFormatter(formatter)
    file_handler.addFilter(filter)
    handlers.append(file_handler)
    _safe_setup_link(logfile_link, logfile_full)
  return handlers


_STDERR_LOGGERS = []
_DISK_LOGGERS = []


def _setup_stderr_logging():
  filter = GenericFilter(lambda r_l: r_l >= LogOptions.stderr_log_level())
  formatter = ProxyFormatter(LogOptions.stderr_log_scheme)
  stderr_handler = logging.StreamHandler(sys.stderr)
  stderr_handler.setFormatter(formatter)
  stderr_handler.addFilter(filter)
  return [stderr_handler]


def teardown_stderr_logging():
  root_logger = logging.getLogger()
  global _STDERR_LOGGERS
  for handler in _STDERR_LOGGERS:
    root_logger.removeHandler(handler)
  _STDERR_LOGGERS = []


def teardown_disk_logging():
  root_logger = logging.getLogger()
  global _DISK_LOGGERS
  for handler in _DISK_LOGGERS:
    root_logger.removeHandler(handler)
  _DISK_LOGGERS = []


def init(filebase=None):
  """
    Sets up default stderr logging and, if filebase is supplied, sets up disk logging using:
      {--log_dir}/filebase.{INFO,WARNING,...}
  """
  logging._acquireLock()

  # set up permissive logger
  root_logger = logging.getLogger()
  root_logger.setLevel(logging.DEBUG)

  # clear existing handlers
  teardown_stderr_logging()
  teardown_disk_logging()
  for handler in root_logger.handlers:
    root_logger.removeHandler(handler)

  # setup INFO...FATAL handlers
  if filebase:
    for handler in _setup_disk_logging(filebase):
      root_logger.addHandler(handler)
      _DISK_LOGGERS.append(handler)
  for handler in _setup_stderr_logging():
    root_logger.addHandler(handler)
    _STDERR_LOGGERS.append(handler)

  logging._releaseLock()

  if len(_DISK_LOGGERS) > 0 and LogOptions.stderr_log_level() != LogOptions.LOG_LEVEL_NONE:
    print('Writing log files to disk in %s' % LogOptions.log_dir(), file=sys.stderr)

  return root_logger
