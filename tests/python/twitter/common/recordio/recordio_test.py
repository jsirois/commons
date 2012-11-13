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

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO

from contextlib import contextmanager
import os
import struct
import tempfile

from twitter.common.recordio import RecordIO
from twitter.common.recordio import RecordWriter, RecordReader
from twitter.common.recordio.filelike import FileLike

import pytest

from recordio_test_harness import DurableFile as DurableFileBase
from recordio_test_harness import EphemeralFile as EphemeralFileBase


class RecordioTestBase(object):
  @classmethod
  @contextmanager
  def DurableFile(cls, mode):
    with DurableFileBase(mode) as fp:
      yield fp

  @classmethod
  @contextmanager
  def EphemeralFile(cls, mode):
    with EphemeralFileBase(mode) as fp:
      yield fp

  def test_paranoid_append_returns_false_on_nonexistent_file(self):
    fn = tempfile.mktemp()
    assert RecordWriter.append(fn, 'hello world!') == False

  def test_basic_recordwriter_write(self):
    test_string = "hello world"
    with self.EphemeralFile('r+') as fp:
      rw = RecordWriter(fp)
      rw.write(test_string)
      fp.seek(0)
      rr = RecordReader(fp)
      assert rr.read() == test_string

  def test_basic_recordwriter_write_synced(self):
    test_string = "hello world"
    with self.EphemeralFile('r+') as fp:
      RecordWriter.do_write(fp, test_string, RecordIO.StringCodec(), sync=True)
      fp.seek(0)
      rr = RecordReader(fp)
      assert rr.read() == test_string

  def test_sanity_check_bytes(self):
    with self.EphemeralFile('r+') as fp:
      fpw = FileLike.get(fp)
      fpw.write(struct.pack('>L', RecordIO.SANITY_CHECK_BYTES+1))
      fpw.write('a')
      fpw.flush()
      fpw.seek(0)

      rr = RecordReader(fp)
      with pytest.raises(RecordIO.RecordSizeExceeded):
        rr.read()

  def test_raises_if_initialized_with_nil_filehandle(self):
    with pytest.raises(RecordIO.InvalidFileHandle):
      RecordWriter(None)
    with pytest.raises(RecordIO.InvalidFileHandle):
      RecordReader(None)

  def test_premature_end_of_stream(self):
    with self.EphemeralFile('r+') as fp:
      fp.write(struct.pack('>L', 1))
      fp.seek(0)
      rr = RecordReader(fp)
      with pytest.raises(RecordIO.PrematureEndOfStream):
        rr.read()

  def test_premature_end_of_stream_mid_message(self):
    with self.EphemeralFile('r+') as fp:
      fp.write(struct.pack('>L', 2))
      fp.write('a')
      fp.seek(0)
      rr = RecordReader(fp)
      with pytest.raises(RecordIO.PrematureEndOfStream):
        rr.read()


class TestRecordioBuiltin(RecordioTestBase):
  def test_recordwriter_framing(self):
    test_string_1 = "hello world"
    test_string_2 = "ahoy ahoy, bonjour"

    with self.EphemeralFile('w') as fp:
      fn = fp.name
      rw = RecordWriter(fp)
      rw.write(test_string_1)
      rw.close()

      with open(fn, 'a') as fpa:
        rw = RecordWriter(fpa)
        rw.write(test_string_2)

      with open(fn) as fpr:
        rr = RecordReader(fpr)
        assert rr.read() == test_string_1
        assert rr.read() == test_string_2

  def test_paranoid_append_framing(self):
    with self.DurableFile('w') as fp:
      fn = fp.name

    test_string_1 = "hello world"
    test_string_2 = "ahoy ahoy, bonjour"

    RecordWriter.append(fn, test_string_1)
    RecordWriter.append(fn, test_string_2)

    with open(fn) as fpr:
      rr = RecordReader(fpr)
      assert rr.read() == test_string_1
      assert rr.read() == test_string_2

    os.remove(fn)

  def test_recordwriter_raises_on_readonly_file(self):
    with self.EphemeralFile('r') as fp:
      with pytest.raises(RecordIO.InvalidFileHandle):
        RecordWriter(fp)

  def test_recordwriter_works_with_append(self):
    with self.EphemeralFile('a') as fp:
      try:
        RecordWriter(fp)
      except:
        assert False, 'Failed to initialize RecordWriter in append mode'

  def test_recordwriter_works_with_readplus(self):
    with self.EphemeralFile('r+') as fp:
      try:
        RecordWriter(fp)
      except:
        assert False, 'Failed to initialize RecordWriter in r+ mode'

  def test_recordwriter_works_with_write(self):
    with self.EphemeralFile('w') as fp:
      try:
        RecordWriter(fp)
      except:
        assert False, 'Failed to initialize RecordWriter in w mode'

  def test_recordreader_works_with_plus(self):
    with self.EphemeralFile('a+') as fp:
      try:
        RecordReader(fp)
      except:
        assert False, 'Failed to initialize RecordWriter in a+ mode'
    with self.EphemeralFile('w+') as fp:
      try:
        RecordReader(fp)
      except:
        assert False, 'Failed to initialize RecordWriter in w+ mode'

  def test_recordreader_fails_with_writeonly(self):
    with self.EphemeralFile('a') as fp:
      with pytest.raises(RecordIO.InvalidFileHandle):
        RecordReader(fp)
    with self.EphemeralFile('w') as fp:
      with pytest.raises(RecordIO.InvalidFileHandle):
        RecordReader(fp)

  def test_basic_recordreader_try_read(self):
    test_string = "hello world"
    with self.EphemeralFile('r') as fp:
      fn = fp.name

      rr = RecordReader(fp)
      assert rr.try_read() is None
      rr.close()

      with open(fn, 'w') as fpw:
        rw = RecordWriter(fpw)
        rw.write(test_string)

      with open(fn) as fpr:
        rr = RecordReader(fpr)
        assert rr.try_read() == test_string

  def test_basic_recordreader_read(self):
    test_string = "hello world"
    with self.EphemeralFile('r') as fp:
      fn = fp.name

      rr = RecordReader(fp)
      assert rr.read() is None
      rr.close()

      with open(fn, 'w') as fpw:
        rw = RecordWriter(fpw)
        rw.write(test_string)

      with open(fn) as fpr:
        rr = RecordReader(fpr)
        assert rr.read() == test_string



class TestRecordioStringIO(RecordioTestBase):
  @classmethod
  @contextmanager
  def EphemeralFile(cls, mode):
    yield StringIO()
