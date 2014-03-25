# TODO (ddavydov) this is needed until all thrift compiled idls are purged from science
publish_properties_files = ['commons/ivy/pushdb/publish.properties', 'twitter/ivy/pushdb/publish.properties']

resources(
  name='build-support',
  sources=rglobs('*') - publish_properties_files,
).with_description('''
Needed by the CI scripts. If this target is changed, CI will build all targets.
''')

