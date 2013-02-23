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

import json
import os
import socket
import sys
import time

from twitter.common import dirutil, log
from twitter.common.process import spawn_daemon
from twitter.common.quantity import Amount, Time
from twitter.common.quantity.parse_simple import parse_time, InvalidTime
from twitter.common.util.command_util import CommandUtil
from twitter.pants import get_buildroot
from twitter.pants.buildtimestats import StatsUploader

STATS_COLLECTION_SECTION = "build-time-stats"
MAX_UPLOAD_DELAY = "stats_collection_max_upload_delay"

PHASE_TOTAL = "phase_total"
CMD_TOTAL = "cmd_total"
PANTS_STATS_FILE_NM = "stats_collection_file"
DEFAULT_STATS_FILE = ".pants.stats"
MAX_RECORDS = 100
__author__ = 'Tejal Desai'

class BuildTimeStats(object):

  def __init__(self, context, cmd=None, socket_ins=None, psutil=None):
    self._cmd = cmd or CommandUtil()
    self._psutil = psutil or None
    self._socket = socket_ins or socket
    self._context = context
    try:
      self._max_delay = parse_time(self._context.config.get(STATS_COLLECTION_SECTION,
                                                            MAX_UPLOAD_DELAY))
    except InvalidTime:
      log.info("Incorrect time string value for stats_collection_max_upload_delay. " +
                "Please fix your ini file")
      self._max_delay = Amount(6, Time.HOURS)

    self._pants_stat_file = (self._context.config.get(STATS_COLLECTION_SECTION,
                                                      PANTS_STATS_FILE_NM) or
                              self._get_default_stats_file()) 

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

  def stats_uploader_daemon(self, stats_file, last_updated_time, debug_max_rec):
    """
    Starts the StatsUploader as a daemon process if it is already not running
    """
    log.debug("Checking if the statsUploaderDaemon is already running")
    stats_pid = os.path.join("/tmp", self._context.config.get("DEFAULT", "user"),
                                      ".pid_stats")
    stats_uploader_dir = os.path.join("/tmp", self._context.config.get("DEFAULT", "user"))
    dirutil.safe_mkdir(stats_uploader_dir)
    if not os.path.exists(stats_pid):
      log.debug("Starting the daemon")
      if spawn_daemon(pidfile=stats_pid, quiet=True):
        su = StatsUploader(self._context, self._max_delay)
        su.upload_sync(stats_file, last_updated_time, debug_max_rec)

  def record_stats(self, timings, elapsed, debug_max_rec=None, stats_file_nm=None):
    """Records all the stats for -x flag
    and the network stats
    """

    timing_stats = self.compute_stats(timings, elapsed)
    stats = {}
    stats["timings"] = timing_stats
    stats["args"] = sys.argv[1:]
    #Get Environment Variable
    stats["env"] = os.environ.data
    stats["timestamp"] = int(time.time())

    try:
      #Get the System info
      if not self._psutil:
        import psutil
        self._psutil = psutil
      stats["cpu_time"] = self._psutil.cpu_percent(interval=1)
      stats["network_counter"] = self._psutil.network_io_counters()
      stats["no_of_cpus"] = self._psutil.NUM_CPUS
    except Exception as e:
      log.debug("Exception %s. Cannot collect psutil stats" % e)

    #Get Git info
    stats["git"] = {}
    (ret, git_origin)= self._cmd.execute_and_get_output(["git", "remote", "-v"])
    if ret == 0:
      for url in git_origin.splitlines():
        origin = url.split()
        str1 = origin[2].strip("(").strip(")")
        if origin:
          stats["git"][str1] = origin[1]

    #Get git branch
    (ret, git_branch) = self._cmd.execute_and_get_output(["git", "rev-parse", "--abbrev-ref",
                                                          "HEAD"])
    if ret == 0:
      stats["git"]["branch"] = git_branch.strip()
    #Network IP
    try:
      stats["ip"] = self._socket.gethostbyname(self._socket.gethostname())
    except Exception as e:
      log.debug("Exception %s. Cannot get ip stats" % e)
    log.debug("Done collecting stats")
    #Read the stats file and check if number of records reached
    stats_file_nm = stats_file_nm if stats_file_nm  else self._pants_stat_file

    #get the last modified time for the File so that we can upload the stats if they havent being
    #Uploaded for last 2 Days.
    last_modified = int(os.path.getmtime(stats_file_nm)) if os.path.exists(stats_file_nm) else None

    try:
      with open(stats_file_nm, 'a') as stats_file:
        json_response = json.dumps(stats, cls=PythonObjectEncoder)
        stats_file.write(json_response+"\n")
      self.stats_uploader_daemon(stats_file_nm, last_modified, debug_max_rec or MAX_RECORDS)
    except IOError as e:
      log.debug("Could not write the pants stats %s" % e)



class PythonObjectEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
      return json.JSONEncoder.default(self, obj)
