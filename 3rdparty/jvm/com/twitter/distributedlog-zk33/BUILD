VERSION='0.2.12'
BK_VERSION='4.2.8-TWTTR-NETTY'

jar_library(name='distributedlog-zk33',
  dependencies=[
    jar(org='com.twitter', name='distributedlog-zk33', rev=VERSION)
      .intransitive().withSources(),
    jar(org='org.apache.bookkeeper', name='bookkeeper-server', rev=BK_VERSION)
      .exclude(org='org.jboss.netty', name='netty'),
    jar(org='org.apache.bookkeeper.shims', name='zookeeper-shim-3.3', rev=BK_VERSION),
    pants('3rdparty/jvm/com/twitter:scrooge-core'),
    pants('3rdparty:jline'),
    pants('3rdparty:junit'),
    pants('3rdparty:libthrift-0.5.0'),
    pants('3rdparty:log4j'),
    pants('3rdparty:netty'),
    pants('3rdparty:slf4j-api'),
    pants(':bk-twitter-science-provider'),
  ]
)

jar_library(name='bk-twitter-science-provider',
  dependencies=[
    jar(org='org.apache.bookkeeper.stats', name='twitter-science-provider', rev=BK_VERSION)
      .intransitive().withSources(),
    jar(org='org.apache.bookkeeper.stats', name='bookkeeper-stats-api', rev=BK_VERSION),
    pants('3rdparty:jetty-8'),
    pants('src/java/com/twitter/common/net/http/handlers'),
    pants('src/java/com/twitter/common/stats:jvm'),
    pants('src/java/com/twitter/common/stats:stats'),
    pants('src/java/com/twitter/common/stats:time-series'),
  ]
)
