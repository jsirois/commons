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

import os
import unittest

from contextlib import closing
from optparse import OptionGroup, OptionParser
from tempfile import mkdtemp
from StringIO import StringIO

from twitter.common.contextutil import temporary_file
from twitter.common.dirutil import safe_open, safe_rmtree

from twitter.pants import set_buildroot
from twitter.pants.base import Address, Config, Target
from twitter.pants.commands.goal import SpecParser
from twitter.pants.goal import Context, Mkflag
from twitter.pants.tasks import Task
from twitter.pants.tasks.console_task import ConsoleTask


def prepare_task(task_type, config=None, args=None, targets=None, **kwargs):
  """Prepares a Task for execution.

  task_type: The class of the Task to create.
  config: An optional string representing the contents of a pants.ini config.
  args: optional list of command line flags, these should be prefixed with '--test-'.
  targets: optional list of Target objects passed on the command line.
  **kwargs: Any additional args the Task subclass constructor takes beyond the required context.

  Returns a new Task ready to execute.
  """

  assert issubclass(task_type, Task), 'task_type must be a Task subclass, got %s' % task_type

  parser = OptionParser()
  option_group = OptionGroup(parser, 'test')
  mkflag = Mkflag('test')
  task_type.setup_parser(option_group, args, mkflag)
  options, _ = parser.parse_args(args or [])

  def load_config():
    with temporary_file() as ini:
      ini.write(config or '')
      ini.close()
      return Config.load()

  context = Context(load_config(), options, targets or [])
  return task_type(context, **kwargs)


class TaskTest(unittest.TestCase):
  """A baseclass useful for testing Tasks."""

  @classmethod
  def build_path(cls, relpath):
    """Returns the canonical BUILD file path for the given relative build path."""
    if os.path.basename(relpath).startswith('BUILD'):
      return relpath
    else:
      return os.path.join(relpath, 'BUILD')

  @classmethod
  def create_target(cls, relpath, target):
    """Adds the given target specification to the BUILD file at relpath.

    relpath: The relative path to the BUILD file from the build root.
    target: A string containing the target definition as it would appear in a BUILD file.
    """
    relpath = cls.build_path(relpath)
    with safe_open(os.path.join(cls.build_root, relpath), 'a') as buildfp:
      buildfp.write(target)

  @classmethod
  def setUpClass(cls):
    cls.build_root = mkdtemp(suffix='_BUILD_ROOT')
    set_buildroot(cls.build_root)

  @classmethod
  def tearDownClass(cls):
    safe_rmtree(cls.build_root)

  @classmethod
  def target(cls, address):
    """Resolves the given target address to a Target object.

    address: The BUILD target address to resolve.

    Returns the corresponding Target or else None if the address does not point to a defined Target.
    """
    return Target.get(Address.parse(cls.build_root, address, is_relative=False))

  @classmethod
  def targets(cls, spec):
    """Resolves a target spec to one or more Target objects.

    spec: Either BUILD target address or else a target glob using the siblings ':' or
          descendants '::' suffixes.

    Returns the set of all Targets found.
    """
    return set(target for target, _ in SpecParser(cls.build_root).parse(spec) if target)


class ConsoleTaskTest(TaskTest):
  """A baseclass useful for testing ConsoleTasks."""

  @classmethod
  def setUpClass(cls):
    super(ConsoleTaskTest, cls).setUpClass()

    task_type = cls.task_type()
    assert issubclass(task_type, ConsoleTask), \
        'task_type() must return a ConsoleTask subclass, got %s' % task_type

  @classmethod
  def task_type(cls):
    """Subclasses must return the type of the ConsoleTask subclass under test."""
    raise NotImplementedError()

  def execute_task(self, config=None, args=None, targets=None):
    """Creates a new task and executes it with the given config, command line args and targets.

    config:  an optional string representing the contents of a pants.ini config.
    args:    optional list of command line flags, these should be prefixed with '--test-'.
    targets: optional list of Target objects passed on the command line.

    Returns the text output of the task.
    """
    with closing(StringIO()) as output:
      task = prepare_task(self.task_type(), config=config, args=args, targets=targets,
                          outstream=output)
      task.execute(targets or [])
      return output.getvalue()

  def execute_console_task(self, config=None, args=None, targets=None, **kwargs):
    """Creates a new task and executes it with the given config, command line args and targets.

    config:   an optional string representing the contents of a pants.ini config.
    args:     optional list of command line flags, these should be prefixed with '--test-'.
    targets:  optional list of Target objects passed on the command line.
    **kwargs: additional kwargs are passed to the task constructor.

    Returns the list of items returned from invoking the console task's console_output method.
    """
    task = prepare_task(self.task_type(), config=config, args=args, targets=targets, **kwargs)
    return list(task.console_output(targets or []))

  def assert_entries(self, sep, *output, **kwargs):
    """Verifies the expected output text is flushed by the console task under test.

    NB: order of entries is not tested, just presence.

    sep:      the expected output separator.
    *output:  the output entries expected between the separators
    **kwargs: additional kwargs are passed to the task constructor except for config args and
              targets which are passed to execute_console_task.
    """
    # We expect each output line to be suffixed with the separator, so for , and [1,2,3] we expect:
    # '1,2,3,' - splitting this by the separator we should get ['1', '2', '3', ''] - always an extra
    # empty string if the separator is properly always a suffix and not applied just between
    # entries.
    self.assertEqual(sorted(list(output) + ['']), sorted((self.execute_task(**kwargs)).split(sep)))

  def assert_console_output(self, *output, **kwargs):
    """Verifies the expected output entries are emitted by the console task under test.

    NB: order of entries is not tested, just presence.

    *output:  the expected output entries
    **kwargs: additional kwargs are passed to the task constructor except for config args and
              targets which are passed to execute_console_task.
    """
    self.assertEqual(sorted(output), sorted(self.execute_console_task(**kwargs)))
