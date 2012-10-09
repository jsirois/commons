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

import os
import tempfile

from contextlib import contextmanager

from twitter.common.contextutil import open_zip

from twitter.pants.java.manifest import Manifest
from twitter.pants.java.nailgun_client import NailgunClient, NailgunError

@contextmanager
def open_jar(path, *args, **kwargs):
  """Yields a jar in a with context that will be closed when the context exits.

  The yielded jar is a zipfile.ZipFile object with an additional mkdirs(arcpath) method that will
  create a zip directory entry similar to unix `mkdir -p`.  Additionally, the ZipFile.write and
  ZipFile.writestr methods are enhanced to call mkdirs as needed to ensure all jar entries contain
  a full complement of parent paths leading from each leaf to the root of the jar.
  """

  with open_zip(path, *args, **kwargs) as jar:
    real_write = jar.write
    real_writestr = jar.writestr

    made_dirs = set()
    def mkdirs(arcpath):
      if arcpath and arcpath not in made_dirs:
        made_dirs.add(arcpath)

        parent_path = os.path.dirname(arcpath)
        mkdirs(parent_path)

        # Any real directory will do so we pick the system tmp dir as a convenient cross-platform
        # available dir.
        real_write(tempfile.gettempdir(), arcpath)

    def write(path, arcname=None, **kwargs):
      mkdirs(os.path.dirname(path)
             if not arcname
             else os.path.dirname(arcname))
      real_write(path, arcname, **kwargs)

    def writestr(zinfo_or_arcname, *args, **kwargs):
      mkdirs(os.path.dirname(zinfo_or_arcname))
      real_writestr(zinfo_or_arcname, *args, **kwargs)

    jar.mkdirs = mkdirs
    jar.write = write
    jar.writestr = writestr

    yield jar


__all__ = (
  open_jar,
  Manifest,
  NailgunClient,
  NailgunError
)
