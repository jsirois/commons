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
Glog log system global options.

Exports module-level options such as --log_dir and --stderr_log_level, but may be
overridden locally before calling log.init().
"""

from __future__ import print_function

import logging
import optparse
import sys

_DISK_LOG_LEVEL_OPTION = 'twitter_common_log_disk_log_level'

_DEFAULT_LOG_OPTS = {
  'twitter_common_log_stderr_log_level': 'ERROR',
  _DISK_LOG_LEVEL_OPTION: 'INFO',
  'twitter_common_log_log_dir': '/var/tmp'
}

try:
  from twitter.common import app
  HAVE_APP = True
except ImportError:
  from collections import namedtuple
  DefaultLogOpts = namedtuple('DefaultLogOpts', _DEFAULT_LOG_OPTS.keys())
  class AppDefaultProxy(object):
    def __init__(self):
      self._opts = DefaultLogOpts(**_DEFAULT_LOG_OPTS)
    def get_options(self):
      return self._opts
    def set_option(self, key, value, force=False):
      opts = self._opts._asdict()
      if force or key not in opts:
        opts[key] = value
  app = AppDefaultProxy()
  HAVE_APP = False

class LogOptionsException(Exception): pass

class LogOptions(object):
  _LOG_LEVEL_NONE_KEY = 'NONE'
  LOG_LEVEL_NONE = 100

  _LOG_LEVELS = {
    'DEBUG':             logging.DEBUG,
    'INFO':              logging.INFO,
    'WARN':              logging.WARN,
    'FATAL':             logging.FATAL,
    'ERROR':             logging.ERROR,
    _LOG_LEVEL_NONE_KEY: LOG_LEVEL_NONE
  }

  _LOG_SCHEMES = [
    'google',
    'plain'
  ]

  _STDERR_LOG_LEVEL = None
  _STDOUT_LOG_SCHEME = None
  _DISK_LOG_LEVEL = None
  _DISK_LOG_SCHEME = None
  _LOG_DIR = None

  @staticmethod
  def _parse_loglevel(log_level, scheme='google'):
    level = None
    components = log_level.split(':')
    if len(components) == 1:
      level = components[0]
    elif len(components) == 2:
      scheme, level = components[0], components[1]
    else:
      raise LogOptionsException("Malformed log level: %s" % log_level)

    if level in LogOptions._LOG_LEVELS:
      level = LogOptions._LOG_LEVELS[level]
    else:
      raise LogOptionsException("Unknown log level: %s" % level)

    if scheme not in LogOptions._LOG_SCHEMES:
      raise LogOptionsException("Unknown log scheme: %s" % scheme)

    return (scheme, level)

  @staticmethod
  def loglevel_name(log_level):
    """
      Return the log level name of the given log_level (integer), or None if it has no name.
    """
    for name, value in LogOptions._LOG_LEVELS.items():
      if value == log_level:
        return name

  @staticmethod
  def _valid_loglevel(log_level):
    try:
      LogOptions._parse_loglevel(log_level)
      return True
    except:
      return False

  @staticmethod
  def set_stderr_log_level(log_level):
    """
      Set the log level for stderr.
    """
    LogOptions._STDOUT_LOG_SCHEME, LogOptions._STDERR_LOG_LEVEL = \
      LogOptions._parse_loglevel(log_level, scheme='plain')

  @staticmethod
  def stderr_log_level():
    """
      Get the current stderr_log_level (in logging units specified by logging module.)
    """
    if LogOptions._STDERR_LOG_LEVEL is None:
      LogOptions.set_stderr_log_level(app.get_options().twitter_common_log_stderr_log_level)
    return LogOptions._STDERR_LOG_LEVEL

  @staticmethod
  def stderr_log_scheme():
    """
      Get the current stderr log scheme.
    """
    if LogOptions._STDOUT_LOG_SCHEME is None:
      LogOptions.set_stderr_log_level(app.get_options().twitter_common_log_stderr_log_level)
    return LogOptions._STDOUT_LOG_SCHEME

  # old deprecated version of these functions.
  set_stdout_log_level = set_stderr_log_level
  stdout_log_level = stderr_log_level
  stdout_log_scheme = stderr_log_scheme

  @staticmethod
  def _is_disk_logging_required():
    return LogOptions._LOG_LEVEL_NONE_KEY != getattr(app.get_options(), _DISK_LOG_LEVEL_OPTION)

  @staticmethod
  def disable_disk_logging():
    """
      Disables disk logging altogether.
    """
    app.set_option(_DISK_LOG_LEVEL_OPTION, LogOptions._LOG_LEVEL_NONE_KEY, force=True)

  @staticmethod
  def set_disk_log_level(log_level):
    """
      Set the log level for disk.
    """
    LogOptions._DISK_LOG_SCHEME, LogOptions._DISK_LOG_LEVEL = \
      LogOptions._parse_loglevel(log_level, scheme='google')

  @staticmethod
  def disk_log_level():
    """
      Get the current disk_log_level (in logging units specified by logging module.)
    """
    if LogOptions._DISK_LOG_LEVEL is None:
      LogOptions.set_disk_log_level(app.get_options().twitter_common_log_disk_log_level)
    return LogOptions._DISK_LOG_LEVEL

  @staticmethod
  def disk_log_scheme():
    """
      Get the current disk log scheme.
    """
    if LogOptions._DISK_LOG_SCHEME is None:
      LogOptions.set_disk_log_level(app.get_options().twitter_common_log_disk_log_level)
    return LogOptions._DISK_LOG_SCHEME

  @staticmethod
  def set_log_dir(dir):
    """
      Set the logging dir for disk logging.  Must be called before log.init() for
      changes to take effect.
    """
    LogOptions._LOG_DIR = dir

  @staticmethod
  def log_dir():
    """
      Get the current directory into which logs will be written.
    """
    if LogOptions._LOG_DIR is None:
      LogOptions._LOG_DIR = app.get_options().twitter_common_log_log_dir
    return LogOptions._LOG_DIR

  @staticmethod
  def _disk_options_callback(option, opt, value, parser):
    try:
      LogOptions.set_disk_log_level(value)
    except LogOptionsException as e:
      raise optparse.OptionValueError('Failed to parse option: %s' % e)
    parser.values.twitter_common_log_disk_log_level = value

  __log_to_stderr_is_set = False
  __log_to_stdout_is_set = False
  @staticmethod
  def _stderr_options_callback(option, opt, value, parser):
    if LogOptions.__log_to_stdout_is_set:
      raise optparse.OptionValueError(
        '--log_to_stdout is an obsolete flag that was replaced by --log_to_stderr. '
        'Use only --log_to_stderr.')
    LogOptions.__log_to_stderr_is_set = True
    try:
      LogOptions.set_stderr_log_level(value)
    except LogOptionsException as e:
      raise optparse.OptionValueError('Failed to parse option: %s' % e)
    parser.values.twitter_common_log_stderr_log_level = value

  @staticmethod
  def _stdout_options_callback(option, opt, value, parser):
    if LogOptions.__log_to_stderr_is_set:
      raise optparse.OptionValueError(
        '--log_to_stdout is an obsolete flag that was replaced by --log_to_stderr. '
        'Use only --log_to_stderr.')
    LogOptions.__log_to_stdout_is_set = True
    print('--log_to_stdout is an obsolete flag that was replaced by '
          '--log_to_stderr. Use --log_to_stderr instead.', file=sys.stderr)
    try:
      LogOptions.set_stderr_log_level(value)
    except LogOptionsException as e:
      raise optparse.OptionValueError('Failed to parse option: %s' % e)
    parser.values.twitter_common_log_stderr_log_level = value

_LOGGING_HELP = \
"""The level at which to log to %%s [default: %%%%default].
Takes either LEVEL or scheme:LEVEL, where LEVEL is one
of %s and scheme is one of %s.
""" % (repr(LogOptions._LOG_LEVELS.keys()), repr(LogOptions._LOG_SCHEMES))

if HAVE_APP:
  app.add_option('--log_to_stdout',
              callback=LogOptions._stdout_options_callback,
              default=_DEFAULT_LOG_OPTS['twitter_common_log_stderr_log_level'],
              type='string',
              action='callback',
              metavar='[scheme:]LEVEL',
              dest='twitter_common_log_stderr_log_level',
              help='OBSOLETE - legacy flag, use --log_to_stderr instead.')

  app.add_option('--log_to_stderr',
              callback=LogOptions._stderr_options_callback,
              default=_DEFAULT_LOG_OPTS['twitter_common_log_stderr_log_level'],
              type='string',
              action='callback',
              metavar='[scheme:]LEVEL',
              dest='twitter_common_log_stderr_log_level',
              help=_LOGGING_HELP % 'stderr')

  app.add_option('--log_to_disk',
              callback=LogOptions._disk_options_callback,
              default=_DEFAULT_LOG_OPTS['twitter_common_log_disk_log_level'],
              type='string',
              action='callback',
              metavar='[scheme:]LEVEL',
              dest='twitter_common_log_disk_log_level',
              help=_LOGGING_HELP % 'disk')

  app.add_option('--log_dir',
              type='string',
              default=_DEFAULT_LOG_OPTS['twitter_common_log_log_dir'],
              metavar='DIR',
              dest='twitter_common_log_log_dir',
              help="The directory into which log files will be generated [default: %default].")
