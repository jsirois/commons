ORG='com.twitter'
SCROOGE_REV='3.12.1'

jar_library(name = 'client-event-util',
  dependencies = [
    jar(org=ORG, name='client-event-util', rev='0.0.1').with_sources(),
  ]
)

jar_library(name = 'twitter-client-user-agent-parser',
  dependencies = [
    jar(org=ORG, name='twitter-client-user-agent-parser', rev='0.0.7').with_sources(),
  ]
)

jar_library(name='iago',
  dependencies=[
    jar(org=ORG, name='iago', rev='0.6.6')
  ]
)

jar_library(name='loglens-logging',
  dependencies=[
    jar(org=ORG, name='loglens-logging', rev='0.0.6')
  ]
)

jar_library(name='scrooge-core',
  dependencies=[
    # used by scrooge-generator described in build-support/profiles/scrooge-gen.ivy.xml
    jar(org=ORG, name='scrooge-core', rev=SCROOGE_REV).with_sources()
  ]
)

jar_library(name='scrooge-runtime',
  dependencies=[
    # used by scrooge-generator described in build-support/profiles/scrooge-gen.ivy.xml
    jar(org=ORG, name='scrooge-runtime', rev=SCROOGE_REV).with_sources()
  ]
)

jar_library(name='scrooge-serializer',
  dependencies=[
    jar(org=ORG, name='scrooge-serializer', rev=SCROOGE_REV).with_sources()
  ]
)

jar_library(name='thumbingbird-thrift-image-fetcher-only',
  dependencies=[
    thrift_jar(org=ORG, name='thumbingbird-thrift-image-fetcher-only', rev='1.1.0')
  ]
)

jar_library(name='thumbingbird-thrift-thumbnail-only',
  dependencies=[
    thrift_jar(org=ORG, name='thumbingbird-thrift-thumbnail-only', rev='1.1.0')
  ]
)

jar_library(name = 'deferredrpc-client',
  dependencies=[
    jar(org=ORG, name='deferredrpc-client', rev='2.0.12') 
  ]
)

jar_library(name = 'scribelib-idl',
  dependencies=[
    thrift_jar(org=ORG, name='scribelib', rev='1.1.55').with_sources(), 
  ]
)
