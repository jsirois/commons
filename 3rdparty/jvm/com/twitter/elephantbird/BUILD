EB_REV = '4.4'
ORG = 'com.twitter.elephantbird'

# DEPRECATED!!!! Use mavenized version instead. Keeping old monojar as-is.
jar_library(name='i-really-should-upgrade-elephant-bird',
  dependencies=[
    jar(org='com.twitter', name='elephant-bird', rev='2.2.3').intransitive()
      .exclude(org = 'org.apache.hadoop', name="hadoop-core")
])

jar_library(name='elephant-bird-hadoop-compat',
  dependencies=[
    jar(org=ORG, name='elephant-bird-hadoop-compat', rev=EB_REV)
      .intransitive()
      .with_sources()
])

jar_library(name='elephant-bird-core',
  dependencies=[
    jar(org=ORG, name='elephant-bird-core', rev=EB_REV)
      .intransitive()
      .with_sources(),
    pants(':elephant-bird-hadoop-compat'),
    pants('3rdparty:guava'),
    pants('3rdparty:hadoop-core'),
    pants('3rdparty:log4j'),
    pants('3rdparty:thrift-0.5.0'),
    pants('3rdparty:json-simple'),
    pants('3rdparty/jvm/com/google/protobuf:protobuf-java-2.4.1'),
    pants('3rdparty/jvm/com/hadoop/gplcompression:hadoop-lzo'),
])

jar_library(name='elephant-bird-cascading2',
  dependencies=[
    jar(org=ORG, name='elephant-bird-cascading2', rev=EB_REV)
      .intransitive()
      .with_sources(),
    pants(':elephant-bird-core'),
])

jar_library(name='elephant-bird-rcfile',
  dependencies=[
    jar(org=ORG, name='elephant-bird-rcfile', rev=EB_REV)
      .intransitive()
      .with_sources(),
    pants(':elephant-bird-core'),
])

jar_library(name='elephant-bird-mahout',
  dependencies=[
    jar(org=ORG, name='elephant-bird-mahout', rev=EB_REV)
      .intransitive()
      .with_sources(),
    pants(':elephant-bird-core'),
])

jar_library(name='elephant-bird-pig',
  dependencies=[
    jar(org=ORG, name='elephant-bird-pig', rev=EB_REV)
      .intransitive()
      .with_sources(),
    pants(':elephant-bird-core'),
    pants('3rdparty/jvm/org/apache/pig'),
])

jar_library(name='elephant-bird-hive',
  dependencies=[
    jar(org=ORG, name='elephant-bird-hive', rev=EB_REV)
      .intransitive()
      .with_sources(),
    pants(':elephant-bird-core'),
])

jar_library(name = 'elephant-bird-lucene',
  dependencies = [
    jar(org=ORG, name = 'elephant-bird-lucene', rev=EB_REV)
      .intransitive()
      .with_sources(),
    pants(':elephant-bird-core'),
    pants('3rdparty/jvm/org/apache/lucene:lucene-core'),
    pants('3rdparty/jvm/org/apache/lucene:lucene-analyzers-common'),
    pants('3rdparty/jvm/org/apache/lucene:lucene-queryparser'),
    jar(org = 'commons-io', name = 'commons-io', rev = '2.4').with_sources(),
])

jar_library(name = 'elephant-bird-pig-lucene',
  dependencies = [
    jar(org=ORG, name = 'elephant-bird-pig-lucene', rev = EB_REV)
      .intransitive()
      .with_sources(),
    pants(':elephant-bird-lucene'),
    pants('3rdparty/jvm/org/apache/pig'),
])
