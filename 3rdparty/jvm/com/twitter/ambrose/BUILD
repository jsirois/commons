AMBROSE_VERSION = '0.3.0'

jar_library(name = 'ambrose-common',
  dependencies = [
    jar(org = 'com.twitter.ambrose', name = 'ambrose-common', rev = AMBROSE_VERSION).with_sources()
      .exclude(org = 'org.mortbay.jetty')
  ],
)

jar_library(name = 'ambrose-pig',
  dependencies = [
    jar(org = 'com.twitter.ambrose', name = 'ambrose-pig', rev = AMBROSE_VERSION).with_sources(),
    pants(':ambrose-common'),
  ],
)
