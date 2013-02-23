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

__author__ = 'Tejal Desai'
import httplib
import os
import sys
import urllib
import time

from twitter.common import dirutil, log
from twitter.common.contextutil import temporary_file
from twitter.common.dirutil.fileset import Fileset
from twitter.common.quantity import Amount, Time

STATS_COLLECTION_SECTION = "build-time-stats"
STATS_COLLECTION_URL = "stats_collection_url"
STATS_COLLECTION_PORT = "stats_collection_port"
STATS_COLLECTION_ENDPOINT = "stats_collection_http_endpoint"
STATS_UPLOADER_PID = "/tmp/%(user)s/.pid_file"


class StatsHttpClient(object):
  def __init__(self, host=None, port=None, http_endpoint=None, stats_dir=None):
    self._client = None
    self._host = host
    self._port = port
    self._http_endpoint = http_endpoint
    self._stats_dir = stats_dir

  def _get_client(self):
    if self._client is None:
      self._client = httplib.HTTPConnection(self._host, self._port, timeout=2)
    return self._client

  def push_stats(self, json_stats):
    log.debug("Uploading pants stats to %s" % self._host)
    client = self._get_client()
    params = urllib.urlencode({"json": json_stats})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    client.request("POST", self._http_endpoint, params, headers)
    resp = client.getresponse()
    resp_type = resp.status / 100
    client.close()
    if resp_type not in [2, 3]:
      log.debug("There was an error uploading the stats")

  def process_stats_file(self):
    for filename in Fileset.walk(self._stats_dir):
      try :
        with open(os.path.join(self._stats_dir, filename), 'r') as stats_file:
          lines = stats_file.readlines()
          tmp_str = ",".join(lines)
          tmp_str.strip(',')
          self.push_stats("[" + tmp_str + "]")
        os.remove(os.path.join(self._stats_dir, filename))
      except httplib.HTTPException as e:
        log.debug("HTTPException %s" % e)
      except OSError as e:
        log.debug("Error creating one of the dirs" % e)


class StatsUploader():
  def __init__(self, context, max_delay):
    self._context = context
    self._stats_dir = os.path.join("/tmp1", self._context.config.get("DEFAULT", "user"),
                                   "stats_uploader_dir")
    self._stats_http_client = StatsHttpClient(
                      self._context.config.get(STATS_COLLECTION_SECTION, STATS_COLLECTION_URL),
                      self._context.config.get(STATS_COLLECTION_SECTION, STATS_COLLECTION_PORT),
                      self._context.config.get(STATS_COLLECTION_SECTION, STATS_COLLECTION_ENDPOINT),
                      self._stats_dir)
    self._max_delay = max_delay

  def upload_sync(self, stats_file_nm, last_modified, max_records):
    try:
      time.sleep(10)
      if not last_modified:
        last_modified = int(os.path.getmtime(stats_file_nm))

      with open(stats_file_nm, 'r') as stats_file:
        lines = stats_file.readlines()
      #Just want to make sure, we do not wait for MAX_RECORDS but also upload when
      #the last time we uploaded is less than configured value in the pants.ini
      last_uploaded = Amount(int(time.time()) - last_modified, Time.SECONDS)
      if (len(lines) >=  max_records or last_uploaded > self._max_delay):
        #Put the file in the right place.
        dirutil.safe_mkdir(self._stats_dir)
        with temporary_file(self._stats_dir, False) as stats_uploader_tmpfile:
          os.rename(stats_file_nm, stats_uploader_tmpfile.name)
        self._stats_http_client.process_stats_file()
      sys.exit(0)
    except OSError as e:
      log.debug("Error creating one of the dirs" % e)
