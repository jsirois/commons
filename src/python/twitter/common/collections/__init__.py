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

__author__ = 'John Sirois'

from sys import version_info

if version_info[0] == 2:
  from .ordereddict import OrderedDict
else:
  from collections import OrderedDict
from .orderedset import OrderedSet
from .ringbuffer import RingBuffer


def maybe_list(value, expected_type=str):
  """
    Given a value that could be a single value or iterable of a particular
    type, always return a list of that type.  By default the expected type
    is a string, but can be specified with the 'expected_type' kwarg, which
    can be a type or tuple of types. Raises ValueError if any type mismatches.
  """
  from collections import Iterable
  if isinstance(value, expected_type):
    return [value]
  elif isinstance(value, Iterable):
    real_values = list(value)
    if not all(isinstance(v, expected_type) for v in real_values):
      raise ValueError('Element of list is not of type %r' % expected_type)
    return real_values
  else:
    raise ValueError('Value must be a %r or iterable of %r' % (expected_type, expected_type))


__all__ = (
  maybe_list,
  OrderedSet,
  OrderedDict,
  RingBuffer,
)
