SERVO_REV = '2.3.0'

jar_library(name='servo-decider',
            dependencies=[
              jar(org='com.twitter', name='servo-decider', rev=SERVO_REV).intransitive().with_sources(),
              pants(':servo-util')
            ])

jar_library(name='servo-repo',
            dependencies=[
              jar(org='com.twitter', name='servo-repo', rev=SERVO_REV).intransitive().with_sources(),
              pants('3rdparty:guava'),
              pants('3rdparty:thrift-0.5.0'),
              pants('3rdparty:finagle-core'),
              pants('3rdparty:finagle-memcached'),
              pants('3rdparty:finagle-thrift'),
              pants('3rdparty/jvm/com/twitter:scrooge-core'),
              pants('3rdparty/jvm/com/twitter:scrooge-serializer'),
              pants('3rdparty:util-core'),
              pants('3rdparty:util-logging'),
              pants(':servo-util'),
            ])

jar_library(name='servo-request',
            dependencies=[
              jar(org='com.twitter', name='servo-request', rev=SERVO_REV).intransitive().with_sources(),
              pants('3rdparty:finagle-core'),
              pants('3rdparty:finagle-thrift'),
              pants('3rdparty:twitter-config-yaml'),
              pants('3rdparty:util-core'),
              pants(':servo-util'),
            ])

jar_library(name='servo-service',
            dependencies=[
              jar(org='com.twitter', name='servo-service', rev=SERVO_REV).intransitive().with_sources(),
              pants('3rdparty:finagle-exception'),
              pants('3rdparty:finagle-memcached'),
              pants('3rdparty:finagle-ostrich4'),
              pants('3rdparty:finagle-serversets'),
              pants('3rdparty:finagle-thrift'),
              pants('3rdparty:finagle-zipkin'),
              pants('3rdparty:ostrich'),
              pants('3rdparty:twitter-config-yaml'),
              pants('3rdparty:util-core'),
              pants('3rdparty:util-logging'),
              pants('3rdparty/jvm/com/twitter:decider'),
              pants(':servo-decider'),
              pants(':servo-request'),
              pants(':servo-util'),
              pants('src/java/com/twitter/common/quantity'),
              pants('src/java/com/twitter/common_internal/zookeeper'),
              pants('src/java/com/twitter/common/zookeeper:client'),
              pants('src/java/com/twitter/common/zookeeper:server-set'),
            ])

jar_library(name='servo-util',
            dependencies=[
              jar(org='com.twitter', name='servo-util', rev=SERVO_REV).intransitive().with_sources(),
              pants('3rdparty:guava'),
              pants('3rdparty:finagle-core'),
              pants('3rdparty:finagle-thrift'),
              pants('3rdparty/jvm/com/twitter:scrooge-core'),
              pants('3rdparty/jvm/com/twitter:scrooge-serializer'),
              pants('3rdparty:util-core'),
              pants('3rdparty:util-logging'),
            ])
