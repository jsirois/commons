from collections import defaultdict

from twitter.pants import get_buildroot
from twitter.pants.base.target import Target
from twitter.pants.base.build_file import BuildFile
from twitter.pants.tasks.console_task import ConsoleTask

class ReverseDepmap(ConsoleTask):
  @classmethod
  def setup_parser(cls, option_group, args, mkflag):
    super(ReverseDepmap, cls).setup_parser(option_group, args, mkflag)
    option_group.add_option(mkflag("transitive"), mkflag("transitive", negate=True),
                            dest="reverse_depmap_transitive", default=False,
                            action="callback", callback=mkflag.set_bool,
                            help="[%default] List transitive dependees.")

  def __init__(self, context):
    ConsoleTask.__init__(self, context)
    self._transitive = context.options.reverse_depmap_transitive

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
    check = set()
    for target in targets:
      check.update(target.resolve())

    known_dependants = set()
    while True:
      dependants = set(known_dependants)
      for target in check:
        dependants.update(dependees_by_target[target])
      check = dependants - known_dependants
      if not check or not self._transitive:
        return dependants - set(targets)
      known_dependants = dependants
