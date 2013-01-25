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

import httplib, urllib

from contextlib import closing
from twitter.common import log


__author__ = 'Tejal Desai'


class StatsHttpClient(object):

  class HTTPError(Exception): pass

  def __init__(self, host=None, port=None, http_endpoint=None):
    self._client = None
    self._host = host
    self._port = port
    self._http_endpoint = http_endpoint

  def _get_client(self):
    if self._client is None:
      self._client = httplib.HTTPConnection(self._host, self._port, timeout=2)
    return self._client

  def push_stats(self, json_stats):
    log.info("Uploading pants stats to %s" % self._host)
    try:
      client = self._get_client()
      params = urllib.urlencode({"json": json_stats})
      headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
      with closing(client.request("POST", self._http_endpoint, params, headers)):
        resp = client.getresponse()
        resp_type = resp.status / 100
        log.info("Recived %s from stats server" % resp.status)
        if resp_type not in [2, 3]:
          raise self.HTTPError(resp.read())
    except Exception as e:
      log.error(e)
      raise self.HTTPError(e)
