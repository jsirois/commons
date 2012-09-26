python_library(
  name = 'serverset',
  sources = globs('*.py') - ['cli.py'],
  dependencies = [
    'src/python/twitter/common/lang',
    'src/python/twitter/common/zookeeper/group',
    'src/thrift/com/twitter/thrift:py-thrift',
  ]
)

python_binary(
  name = 'cli',
  source = 'cli.py',
  dependencies = [
    pants('src/python/twitter/common/app'),
    pants(':serverset')
  ],
)
