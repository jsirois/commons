from collections import defaultdict

from twitter.pants import get_buildroot
from twitter.pants.base.target import Target
from twitter.pants.base.build_file import BuildFile
from twitter.pants.tasks.console_task import ConsoleTask

class ReverseDepmap(ConsoleTask):
  def console_output(self, targets):
    dependees_by_target = defaultdict(set)
    for buildfile in BuildFile.scan_buildfiles(get_buildroot()):
      for address in Target.get_all_addresses(buildfile):
        for target in Target.get(address).resolve():
          if hasattr(target, 'dependencies'):
            for dependencies in target.dependencies:
              for dependency in dependencies.resolve():
                dependees_by_target[dependency].add(target)

    for dependant in self.get_dependants(dependees_by_target, self.context.target_roots):
      yield dependant.address

  def get_dependants(self, dependees_by_target, targets):
    dependants = set()
    core = set(targets)
    while True:
      for target in core:
        dependants.add(target)
        dependants.update(dependees_by_target[target])
      core.update(dependants)
      if core == dependants:
        return dependants - set(targets)
