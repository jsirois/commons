PQ_REV = '1.3.2'

# parquet-cascading depends on new version of elephantbird which pulls in thrift 0.7, here force it
# to use thrift 0.5 to be compatible with science repo
thrift = pants('3rdparty:libthrift-0.5.0').get()
thrift.force = True

# Target that references this target may need to exclude org.apache.hadoop using deploy_excludes to
# prevent hadoop jars gets pulled in
# It also pulls in org.codehaus.jackson, exclude it if you have a different/uncompatible version of
# it

def make_parquet_lib(libname):
  return jar_library(name=libname,
    dependencies=[
      thrift,
      jar(org='com.twitter', name=libname, rev=PQ_REV)
        .exclude(org='org.apache.hadoop')
        .exclude(org = 'org.codehaus.janino', name = 'janino'),
    ],
  )


make_parquet_lib('parquet-cascading')
make_parquet_lib('parquet-scrooge')
