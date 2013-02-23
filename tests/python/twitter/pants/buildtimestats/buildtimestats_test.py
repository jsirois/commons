__author__ = 'Tejal Desai'

import json
import os
import tempfile
import unittest

from twitter.common.dirutil.fileset import Fileset
from twitter.pants.buildtimestats import BuildTimeStats as RealBuildTimeStats


class BuildTimeStats(RealBuildTimeStats):
  def get_stats(self):
    return self.json_str

  def stats_uploader_daemon(self):
    stats_upload_dir = self._context.config.get("stats_test","stats_uploader_dir" )
    for filename in Fileset.walk(stats_upload_dir):
      with open(os.path.join(stats_upload_dir, filename), 'r') as stats_file:
       lines = stats_file.readlines()
       tmp_str = ",".join(lines)
       tmp_str.strip(',')
      self.json_str = "[" + tmp_str + "]"
      os.unlink(stats_file)

class MockPsUtil:
  NUM_CPUS = 1
  @staticmethod
  def cpu_percent(interval):
    return 1.0
  @staticmethod
  def network_io_counters():
    return "1000,10000,1000"

class MockContext:
  def __init__(self):
    self.config = Mockconfig()


class Mockconfig:
  def get(self, section, val):
    if val == "stats_collection_url":
      return "http://build_time_stats_collector.smf1.devprod.service.smf1.twitter.com"
    elif val == "stats_collection_port":
      return "8080"
    elif val == "stats_collection_max_upload_delay":
      return "6h"
    elif val =="stats_collection_file":
      return "pants.stats"
    elif val == "stats_uploader_dir":
      return "/tmp/stats_file"
    elif val == "stats_uploader_pid_file":
      return "/tmp/.pid_file"


class MockCommandUtil:
  @staticmethod
  def execute_and_get_output(cmd):
    if cmd[1] == "remote":
      return (0, "origin  https://git.twitter.biz/science (fetch)\norigin  https://git.twitter.biz/science (push)")
    if cmd[1] == "rev-parse":
      return (0, "test_br")


class MockSocket:
  @staticmethod
  def gethostbyname(args):
    return "localhost"
  @staticmethod
  def gethostname():
    return "localhost"

class BuildTimeStatsTest(unittest.TestCase):
  def test_compute_stats(self):
    executed_goals = {'resolve-idl':{ 'idl': [0.00072813034057617188],
                                      'extract': [3.0994415283203125e-06] },
                      "thriftstore-codegen": {'thriftstore-codegen': [0.0001010894775390625] },
                      "gen": {'tweetypie-fetch': [0.028632879257202148], 'thrift': [0.016566991806030273],
                              'protoc': [0.0038318634033203125], 'antlr': [0.0020389556884765625],
                              'thriftstore-dml-gen': [0.0022170543670654297],
                              'tweetypie-clean': [0.0054290294647216797] },
                      "resolve": {'ivy': [0.00097703933715820312] },
                      "compile": {'checkstyle': [0.00057005882263183594]},
                      "test": {'junit': [9.1075897216796875e-05], 'specs': [0.0015749931335449219]}
                    }
    bs = BuildTimeStats(MockContext(), MockCommandUtil, MockSocket, MockPsUtil)
    actual_timings = bs.compute_stats(executed_goals, 100)
    expected_timings =[{'phase': 'resolve', 'total': 0.00097703933715820312, 'goal': 'ivy'},
                       {'phase': 'resolve-idl', 'total': 0.00072813034057617188, 'goal': 'idl'},
                       {'phase': 'resolve-idl', 'total': 3.0994415283203125e-06, 'goal': 'extract'},
                       {'phase': 'resolve-idl', 'total': 0.00073122978210449219, 'goal': 'phase_total'},
                       {'phase': 'compile', 'total': 0.00057005882263183594, 'goal': 'checkstyle'},
                       {'phase': 'thriftstore-codegen', 'total': 0.0001010894775390625, 'goal': 'thriftstore-codegen'},
                       {'phase': 'test', 'total': 9.1075897216796875e-05, 'goal': 'junit'},
                       {'phase': 'test', 'total': 0.0015749931335449219, 'goal': 'specs'},
                       {'phase': 'test', 'total': 0.0016660690307617188, 'goal': 'phase_total'},
                       {'phase': 'gen', 'total': 0.0038318634033203125, 'goal': 'protoc'},
                       {'phase': 'gen', 'total': 0.0020389556884765625, 'goal': 'antlr'},
                       {'phase': 'gen', 'total': 0.028632879257202148, 'goal': 'tweetypie-fetch'},
                       {'phase': 'gen', 'total': 0.0054290294647216797, 'goal': 'tweetypie-clean'},
                       {'phase': 'gen', 'total': 0.0022170543670654297, 'goal': 'thriftstore-dml-gen'},
                       {'phase': 'gen', 'total': 0.016566991806030273, 'goal': 'thrift'},
                       {'phase': 'gen', 'total': 0.058716773986816406, 'goal': 'phase_total'},
                       {'phase': 'cmd_total', 'total': 100, 'goal': 'cmd_total'}]
    self.assertEqual(actual_timings, expected_timings )


  def test_record_stats(self):
    timings =  {"compile": {'checkstyle': [0.00057005882263183594]}}

    bs = BuildTimeStats(MockContext(), MockCommandUtil, MockSocket, MockPsUtil)
    temp_filename = tempfile.mktemp()

    bs.record_stats(timings, 100, 1, temp_filename)

    json_str = bs.get_stats()
    stats = json.loads(json_str)
    self.assertTrue(len(stats) ==1)
    self.assertTrue(stats[0].has_key("cpu_time"))
    self.assertTrue(stats[0].has_key("timings"))
    self.assertTrue(stats[0].has_key("ip"))
    self.assertTrue(stats[0].has_key("env"))
    self.assertEquals(stats[0]['git']['push'], "https://git.twitter.biz/science")
    self.assertEquals(stats[0]['git']['branch'], "test_br")

  def test_record_stats_written(self):
    timings =  {"compile": {'checkstyle': [0.00057005882263183594]}}
    bs = BuildTimeStats(MockContext(), MockCommandUtil, MockSocket, MockPsUtil)
    temp_filename = tempfile.mktemp()

    bs.record_stats(timings, 100, 2, temp_filename)
    self.assertTrue(os.path.exists(temp_filename))

    #Test append
    timings =  {"compile": {'checkstyle': [0.00057005882263183594]}}
    bs.record_stats(timings, 100, 3, temp_filename)
    self.assertTrue(os.path.exists(temp_filename))
    with open(temp_filename, 'r') as stats_file:
      lines = stats_file.readlines()
    self.assertEquals(len(lines),2)
    os.remove(temp_filename)
