jar_library(name = 'hraven-core',
  dependencies = [
    jar(org = 'com.twitter.hraven', name = 'hraven-core', rev = '0.9.2').with_sources()
      .exclude(org = 'com.twitter.common')
      .exclude(org = 'com.twitter.common_internal.zookeeper')
      .exclude(org = 'org.mortbay.jetty'),
    jar(org = 'org.apache.hbase', name = 'hbase', rev = '0.94.t1'),
    pants('src/java/com/twitter/common/application'),
    pants('src/java/com/twitter/common/application/modules:http'),
    pants('src/java/com/twitter/common/application/modules:log'),
    pants('src/java/com/twitter/common/application/modules:stats'),
    pants('src/java/com/twitter/common/application/modules:lifecycle'),
  ],
)
