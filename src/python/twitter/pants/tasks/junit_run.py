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
import re
import sys

from twitter.common.dirutil import safe_mkdir, safe_open

from twitter.pants import binary_util, is_codegen, is_java, is_scala, is_test, junit_tests
from twitter.pants.tasks import Task, TaskError
from twitter.pants.tasks.jvm_task import JvmTask

class JUnitRun(JvmTask):
  @classmethod
  def setup_parser(cls, option_group, args, mkflag):
    option_group.add_option(mkflag("skip"), mkflag("skip", negate=True), dest = "junit_run_skip",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%default] Skip running tests")

    option_group.add_option(mkflag("debug"), mkflag("debug", negate=True), dest = "junit_run_debug",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%default] Run junit tests with a debugger")

    option_group.add_option(mkflag("fail-fast"), mkflag("fail-fast", negate=True),
                            dest = "junit_run_fail_fast",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%default] Fail fast on the first test failure in a suite")

    option_group.add_option(mkflag("batch-size"), type = "int", default=sys.maxint,
                            dest = "junit_run_batch_size",
                            help = "[ALL] Runs at most this many tests in a single test process.")

    option_group.add_option(mkflag("jvmargs"), dest = "junit_run_jvmargs", action="append",
                            help = "Runs junit tests in a jvm with these extra jvm args.")

    option_group.add_option(mkflag("test"), dest = "junit_run_tests", action="append",
                            help = "[%default] Force running of just these tests.  Tests can be "
                                   "specified using any of: [classname], [classname]#[methodname], "
                                   "[filename] or [filename]#[methodname]")

    outdir = mkflag("outdir")
    option_group.add_option(outdir, dest="junit_run_outdir",
                            help="Emit output in to this directory.")

    xmlreport = mkflag("xmlreport")
    option_group.add_option(xmlreport, mkflag("xmlreport", negate=True),
                            dest = "junit_run_xmlreport",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%default] Causes an xml report to be output for each test "
                                   "class that is run.")

    option_group.add_option(mkflag("per-test-timer"), mkflag("per-test-timer", negate=True),
                            dest = "junit_run_per_test_timer",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%default] Shows progress and timer for each test "
                                   "class that is run.")

    option_group.add_option(mkflag("default-parallel"), mkflag("default-parallel", negate=True),
                            dest = "junit_run_default_parallel",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%default] Whether to run classes without @TestParallel or "
                                   "@TestSerial annotations in parallel.")

    option_group.add_option(mkflag("parallel-threads"), type = "int", default=0,
                            dest = "junit_run_parallel_threads",
                            help = "Number of threads to run tests in parallel. 0 for autoset.")

    option_group.add_option(mkflag("coverage"), mkflag("coverage", negate=True),
                            dest = "junit_run_coverage",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%default] Collects code coverage data")

    coverage_patterns = mkflag("coverage-patterns")
    option_group.add_option(coverage_patterns, dest="junit_run_coverage_patterns",
                            action="append",
                            help="By default all non-test code depended on by the selected tests "
                                 "is measured for coverage during the test run.  By specifying "
                                 "coverage patterns you can select which classes and packages "
                                 "should be counted.  Values should be class name prefixes in "
                                 "dotted form with ? and * wildcard support. If preceded with a - "
                                 "the pattern is excluded. "
                                 "For example, to include all code in com.twitter.raven except "
                                 "claws and the eye you would use: "
                                 "%(flag)s=com.twitter.raven.* "
                                 "%(flag)s=-com.twitter.raven.claw "
                                 "%(flag)s=-com.twitter.raven.Eye"
                                 "This option can be specified multiple times. " % dict(
                                    flag=coverage_patterns
                                 ))

    option_group.add_option(mkflag("coverage-console"), mkflag("coverage-console", negate=True),
                            dest = "junit_run_coverage_console",
                            action="callback", callback=mkflag.set_bool, default=True,
                            help = "[%default] Outputs a simple coverage report to the console.")

    option_group.add_option(mkflag("coverage-xml"), mkflag("coverage-xml", negate=True),
                            dest = "junit_run_coverage_xml",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%%default] Produces an xml coverage report in %s." % outdir)

    coverage_html_flag = mkflag("coverage-html")
    option_group.add_option(coverage_html_flag, mkflag("coverage-html", negate=True),
                            dest = "junit_run_coverage_html",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%%default] Produces an html coverage report in %s." % outdir)

    option_group.add_option(mkflag("coverage-html-open"), mkflag("coverage-html-open", negate=True),
                            dest = "junit_run_coverage_html_open",
                            action="callback", callback=mkflag.set_bool, default=False,
                            help = "[%%default] Tries to open the generated html coverage report, "
                                   "implies %s." % coverage_html_flag)

    option_group.add_option(mkflag("suppress-output"), mkflag("suppress-output", negate=True),
                            dest = "junit_run_suppress_output",
                            action="callback", callback=mkflag.set_bool, default=True,
                            help = "[%%default] Redirects test output to files in %s.  "
                                   "Implied by %s" % (outdir, xmlreport))

  def __init__(self, context):
    Task.__init__(self, context)

    self.confs = context.config.getlist('junit-run', 'confs')
    self.junit_profile = context.config.get('junit-run', 'junit_profile')
    self.emma_profile = context.config.get('junit-run', 'emma_profile')

    self.java_args = context.config.getlist('junit-run', 'args', default=[])
    if context.options.junit_run_jvmargs:
      self.java_args.extend(context.options.junit_run_jvmargs)
    if context.options.junit_run_debug:
      self.java_args.extend(context.config.getlist('jvm', 'debug_args'))

    self.test_classes = context.options.junit_run_tests
    self.context.products.require('classes')

    self.outdir = (
      context.options.junit_run_outdir
      or context.config.get('junit-run', 'workdir')
    )

    self.batch_size = context.options.junit_run_batch_size
    self.fail_fast = context.options.junit_run_fail_fast

    self.coverage = context.options.junit_run_coverage
    self.coverage_filters = context.options.junit_run_coverage_patterns or []
    self.coverage_dir = os.path.join(self.outdir, 'coverage')
    self.coverage_instrument_dir = os.path.join(self.coverage_dir, 'classes')
    self.coverage_metadata_file = os.path.join(self.coverage_dir, 'coverage.em')
    self.coverage_file = os.path.join(self.coverage_dir, 'coverage.ec')

    self.coverage_report_console = context.options.junit_run_coverage_console
    self.coverage_console_file = os.path.join(self.coverage_dir, 'coverage.txt')

    self.coverage_report_xml = context.options.junit_run_coverage_xml
    self.coverage_xml_file = os.path.join(self.coverage_dir, 'coverage.xml')

    self.coverage_report_html_open = context.options.junit_run_coverage_html_open
    self.coverage_report_html = (
      self.coverage_report_html_open
      or context.options.junit_run_coverage_html
    )
    self.coverage = self.coverage or self.coverage_report_html_open
    self.coverage_html_file = os.path.join(self.coverage_dir, 'html', 'index.html')

    self.opts = []
    if context.options.junit_run_xmlreport or context.options.junit_run_suppress_output:
      if self.fail_fast:
        self.opts.append('-fail-fast')
      if context.options.junit_run_xmlreport:
        self.opts.append('-xmlreport')
      self.opts.append('-suppress-output')
      self.opts.append('-outdir')
      self.opts.append(self.outdir)

    if context.options.junit_run_per_test_timer:
      self.opts.append('-per-test-timer')
    if context.options.junit_run_default_parallel:
      self.opts.append('-default-parallel')
    self.opts.append('-parallel-threads')
    self.opts.append(str(context.options.junit_run_parallel_threads))

  def _partition(self, tests):
    stride = min(self.batch_size, len(tests))
    for i in xrange(0, len(tests), stride):
      yield tests[i:i+stride]

  def execute(self, targets):
    if not self.context.options.junit_run_skip:
      tests = list(self.normalize_test_classes() if self.test_classes
                                                 else self.calculate_tests(targets))
      if tests:
        junit_classpath = self.classpath(binary_util.profile_classpath(self.junit_profile),
                                         confs=self.confs)

        def run_tests(classpath, main, jvmargs=None):
          # TODO(John Sirois): Integrated batching with the test runner.  As things stand we get
          # results summaries for example for each batch but no overall summary.
          # http://jira.local.twitter.com/browse/AWESOME-1114
          result = 0
          for batch in self._partition(tests):
            with binary_util.safe_args(batch) as batch_tests:
              result += abs(binary_util.runjava_indivisible(
                jvmargs=(jvmargs or []) + self.java_args,
                classpath=classpath,
                main=main,
                opts=self.opts, args=batch_tests
              ))
              if result != 0 and self.fail_fast:
                break
          if result != 0:
            raise TaskError()

        if self.coverage:
          emma_classpath = binary_util.profile_classpath(self.emma_profile)

          def instrument_code():
            safe_mkdir(self.coverage_instrument_dir, clean=True)
            with binary_util.safe_args(self.get_coverage_patterns(targets)) as patterns:
              opts = [
                'instr',
                '-out', self.coverage_metadata_file,
                '-d', self.coverage_instrument_dir,
                '-cp', os.pathsep.join(junit_classpath),
                '-exit'
              ]
              for pattern in patterns:
                opts.extend(['-filter', pattern])
              result = binary_util.runjava_indivisible(classpath=emma_classpath, main='emma',
                                                       opts=opts)
              if result != 0:
                raise TaskError('Emma instrumentation failed with: %d' % result)

          def generate_reports():
            opts = [
              'report',
              '-in', self.coverage_metadata_file,
              '-in', self.coverage_file,
              '-exit'
            ]
            source_bases = set()
            def collect_source_base(target):
              if self.is_coverage_target(target):
                source_bases.add(target.target_base)
            for target in self.test_target_candidates(targets):
              target.walk(collect_source_base)
            for source_base in source_bases:
              opts.extend(['-sp', source_base])

            sorting = ['-Dreport.sort', '+name,+class,+method,+block']
            if self.coverage_report_console:
              opts.extend(['-r', 'txt',
                           '-Dreport.txt.out.file=%s' % self.coverage_console_file] + sorting)
            if self.coverage_report_xml:
              opts.extend(['-r', 'xml','-Dreport.xml.out.file=%s' % self.coverage_xml_file])
            if self.coverage_report_html:
              opts.extend(['-r', 'html',
                           '-Dreport.html.out.file=%s' % self.coverage_html_file,
                           '-Dreport.out.encoding=UTF-8'] + sorting)

            result = binary_util.runjava_indivisible(
              classpath=emma_classpath,
              main='emma',
              opts=opts
            )
            if result != 0:
              raise TaskError('Failed to emma generate code coverage reports: %d' % result)

            if self.coverage_report_console:
              with safe_open(self.coverage_console_file) as console_report:
                sys.stdout.write(console_report.read())
            if self.coverage_report_html_open:
              binary_util.open(self.coverage_html_file)

          instrument_code()
          try:
            # Coverage runs over instrumented classes require the instrumented classes come 1st in
            # the classpath followed by the normal classpath.  The instrumentation also adds a
            # dependency on emma libs that must be satisfied on the classpath.
            run_tests(
              [self.coverage_instrument_dir] + junit_classpath + emma_classpath,
              'com.twitter.common.testing.runner.JUnitConsoleRunner',
              jvmargs=['-Demma.coverage.out.file=%s' % self.coverage_file]
            )
          finally:
            generate_reports()
        else:
          run_tests(junit_classpath, 'com.twitter.common.testing.runner.JUnitConsoleRunner')

  def is_coverage_target(self, tgt):
    return (is_java(tgt) or is_scala(tgt)) and not is_test(tgt) and not is_codegen(tgt)

  def get_coverage_patterns(self, targets):
    if self.coverage_filters:
      return self.coverage_filters
    else:
      classes_under_test = set()
      classes_by_source = self.context.products.get('classes')
      def add_sources_under_test(tgt):
        if self.is_coverage_target(tgt):
          for source in tgt.sources:
            classes = classes_by_source.get(source)
            if classes:
              for base, classes in classes.items():
                classes_under_test.update(
                  JUnitRun.classfile_to_classname(cls) for cls in classes
                )

      for target in targets:
        target.walk(add_sources_under_test)
      return classes_under_test

  def normalize_test_classes(self):
    for cls in self.test_classes:
      for c in self.normalize(cls):
        yield c

  def test_target_candidates(self, targets):
    for target in targets:
      if isinstance(target, junit_tests):
        yield target

  def calculate_tests(self, targets):
    for target in self.test_target_candidates(targets):
      for test in target.sources:
        for cls in self.normalize(test, target.target_base):
          yield cls

  @staticmethod
  def classfile_to_classname(cls):
    clsname, _ = os.path.splitext(cls.replace('/', '.'))
    return clsname

  def normalize(self, classname_or_file, basedir=None):
    components = classname_or_file.split('#', 2)
    classname = components[0]
    methodname = '#' + components[1] if len(components) == 2 else ''

    classes_by_source = self.context.products.get('classes')
    def relpath_toclassname(path):
      classes = classes_by_source.get(path)
      if not classes:
        # Its perfectly valid - if questionable - to have a source file with no classes when, for
        # example, the source file has all its code commented out.
        self.context.log.warn('File %s contains no classes' % os.path.join(basedir, path))
      else:
        for base, classes in classes.items():
          for cls in classes:
            yield JUnitRun.classfile_to_classname(cls)

    if basedir:
      for classname in relpath_toclassname(classname):
        yield classname + methodname
    elif os.path.exists(classname):
      basedir = calculate_basedir(classname)
      for classname in relpath_toclassname(os.path.relpath(classname, basedir)):
        yield classname + methodname
    else:
      yield classname + methodname

PACKAGE_PARSER = re.compile(r'^\s*package\s+([\w.]+)\s*;?\s*')

def calculate_basedir(file):
  with open(file, 'r') as source:
    for line in source:
      match = PACKAGE_PARSER.match(line)
      if match:
        package = match.group(1)
        packagedir = package.replace('.', '/')
        dir = os.path.dirname(file)
        if not dir.endswith(packagedir):
          raise TaskError('File %s declares a mismatching package %s' % (file, package))
        return dir[:-len(packagedir)]

  raise TaskError('Could not calculate a base dir for: %s' % file)
