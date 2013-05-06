# Analytics maintains "pig" as the current production version.
# Please use unless you have a good reason to use an older release.

PIG_VERSION='0.11.2+80'

jar_library(name='pig',
  dependencies=[
    pants('3rdparty:antlr-3.4'),
    pants('3rdparty:commons-logging'),
    pants('3rdparty:jackson-core-asl'),
    pants('3rdparty:jackson-mapper-asl'),
    pants('3rdparty:jline'),
    pants('3rdparty/jvm/commons-cli'),
    jar(org='commons-httpclient', name='commons-httpclient', rev='3.1'),
    jar(org='org.apache.pig', name='pig', rev=PIG_VERSION)
      .intransitive()
      .with_sources(),
])

jar_library(name='pig-core',
  dependencies=[
    jar(org='org.apache.pig', name='pig', rev=PIG_VERSION).intransitive()
])

jar_library(name='pig-9',
  dependencies=[
    jar(org='org.apache.pig', name='pig', rev='0.9.2+20').intransitive()
])
