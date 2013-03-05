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

import os
import sys
import time

from twitter.common import dirutil, log
from twitter.common.process import spawn_daemon
from twitter.common.quantity import Amount, Time
from twitter.common.quantity.parse_simple import parse_time, InvalidTime
from twitter.pants import get_buildroot
from twitter.pants.buildtimestats import StatsUploader

STATS_COLLECTION_SECTION = "build-time-stats"
MAX_UPLOAD_DELAY = "stats_collection_max_upload_delay"
STATS_COLLECTION_URL = "stats_collection_url"
STATS_COLLECTION_PORT = "stats_collection_port"
STATS_COLLECTION_ENDPOINT = "stats_collection_http_endpoint"
MAX_UPLOAD_DELAY = "stats_collection_max_upload_delay"
PANTS_STATS_FILE_NM = "stats_collection_file"
DEFAULT_STATS_FILE = ".pants.stats"
PHASE_TOTAL = "phase_total"
CMD_TOTAL = "cmd_total"

__author__ = 'Tejal Desai'

class BuildTimeStats(object):

  def __init__(self, context, cmd=None):
    self._context = context
    try:
      self._max_delay = parse_time(self._context.config.get(STATS_COLLECTION_SECTION,
                                                            MAX_UPLOAD_DELAY))
    except InvalidTime:
      log.warn("Incorrect time string value for stats_collection_max_upload_delay. " +
               "Please fix your ini file")
      self._max_delay = Amount(6, Time.HOURS)

  def _get_default_stats_file(self):
    return os.path.join(get_buildroot(), DEFAULT_STATS_FILE)

  def compute_stats(self, executed_goals, elapsed):
    timings_array = []
    for phase, timings in executed_goals.items():
      phase_time = None
      for goal, times in timings.items():
        #Create a new structure
        timing = dict()
        timing['phase'] = str(phase)
        timing['goal']  = goal
        timing['total'] = sum(times)
        if not phase_time:
          phase_time = 0
        phase_time += sum(times)
        #Add the timings for each sub phase in the timings array
        timings_array.append(timing)
      if len(timings) > 1:
        #Add the phase total
        timing = dict()
        timing['phase'] = str(phase)
        timing['goal']  = PHASE_TOTAL
        timing['total'] = phase_time
        timings_array.append(timing)
    #end of Loop through PHASES
    timing = {}
    timing['phase'] = CMD_TOTAL
    timing['goal']  = CMD_TOTAL
    timing['total'] = elapsed
    timings_array.append(timing)
    return timings_array

  def get_user(self):
    return self._context.config.getdefault("user")

  def stats_uploader_daemon(self, stats):
    """
    Starts the StatsUploader as a daemon process if it is already not running
    """
    log.debug("Checking if the statsUploaderDaemon is already running")
    user = self.get_user()
    stats_pid = os.path.join("/tmp", user, ".pid_stats")
    stats_uploader_dir = os.path.join("/tmp", )
    dirutil.safe_mkdir(stats_uploader_dir)
    if not os.path.exists(stats_pid):
      log.debug("Starting the daemon")
      stats_log_file = os.path.join("/tmp", user, "buildtime_uploader")
      log.debug("The logs are writen to %s" % stats_log_file)
      if spawn_daemon(pidfile=stats_pid, quiet=True):
        force_stats_upload = False
        if "--force_stats_upload" in sys.argv:
          force_stats_upload = True
        su = StatsUploader(self._context.config.get(STATS_COLLECTION_SECTION, STATS_COLLECTION_URL),
                           self._context.config.get(STATS_COLLECTION_SECTION, STATS_COLLECTION_PORT),
                           self._context.config.get(STATS_COLLECTION_SECTION, STATS_COLLECTION_ENDPOINT),
                           self._max_delay,
                           self._context.config.get(STATS_COLLECTION_SECTION, PANTS_STATS_FILE_NM) or
                           self._get_default_stats_file(),
                           user,
                           force_stats_upload)
        su.upload_sync(stats)

  def record_stats(self, timings, elapsed):
    """Records all the stats for -x flag
    and the network stats
    """
    timing_stats = self.compute_stats(timings, elapsed)
    stats = {}
    stats["timings"] = timing_stats
    stats["args"] = sys.argv[1:]
    self.stats_uploader_daemon(stats)
