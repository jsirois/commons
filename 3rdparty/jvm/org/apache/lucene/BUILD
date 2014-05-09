#
# Please update Lucene Version with caution. It could break several services, and affect
# the ability to load long-lived indexes stored on HDFS.
#

def lucene_jar_library(name, jar_name, rev, force=False):
  jar_library(name = name,
              dependencies = [
              jar(org = 'org.apache.lucene',
                  name = jar_name,
                  rev = rev,
                  force = force).withSources()])

LUCENE_TARGETS = ('lucene-analyzers-common',
                  'lucene-core',
                  'lucene-queries',
                  'lucene-spatial',
                  'lucene-queryparser',
                  'lucene-test-framework',
                  'lucene-analyzers-smartcn',
                  'lucene-facet',
                  'lucene-suggest')

# Default targets without version numbers.
for t in LUCENE_TARGETS:
  lucene_jar_library(t, t, '4.4.0')

# Make explicitly versioned targets
# Please do not delete existing targets, make new ones.
# This is important because we don't want these target to ever change without warning
# as it can cause long-lived indexes stored on disk or in HDFS to become unreadable.
for t in LUCENE_TARGETS:
  lucene_jar_library(t + '-4.1.0', t, '4.1.0', force = True)

for t in LUCENE_TARGETS:
  lucene_jar_library(t + '-4.4.0', t, '4.4.0', force = True)
