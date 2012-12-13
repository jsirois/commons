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

from Queue import Queue, Empty
from threading import Thread

from twitter.common.lang import Compatibility
from twitter.common.quantity import Amount, Time

from concurrent.futures import *
from .deferred import defer


class Timeout(Exception):
  pass

def deadline(closure, timeout=Amount(150, Time.MILLISECONDS)):
  """Run a closure with a timeout, raising an exception if the timeout is exceeded.

    Args:
      closure - function to be run (e.g. functools.partial, or lambda)
    Keyword args:
      timeout - in seconds, or Amount of Time, [default: Amount(150, Time.MILLISECONDS]
  """
  if isinstance(timeout, Compatibility.numeric):
    pass
  elif isinstance(timeout, Amount) and isinstance(timeout.unit(), Time):
    timeout = timeout.as_(Time.SECONDS)
  else:
    raise ValueError('timeout must be either numeric or Amount of Time.')
  q = Queue(maxsize=1)
  class AnonymousThread(Thread):
    def run(self):
      q.put(closure())
  AnonymousThread().start()
  try:
    return q.get(timeout=timeout)
  except Empty:
    raise Timeout("Timeout exceeded!")
