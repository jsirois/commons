#
# Please update Version with caution. It could break several services.
#

# opennlp-maxent-3.0.3 depends on junit in pom. So we setup it manually
# to exclude junit here.
jar_library(name='opennlp-maxent-3.0.3',
  dependencies=[
    jar(org='org.apache.opennlp', name='opennlp-maxent', rev='3.0.3')
      .intransitive()
      .with_sources(),
])

# opennlp-tools-1.5.3 depends on OSGI, junit, and jwnl in pom, while
# only jwnl is actually used. So we manually setup the dependencies here.
# jwnl 1.3.3 does not have dependency.
jar_library(name='opennlp-tools-1.5.3',
  dependencies=[
    jar(org='org.apache.opennlp', name='opennlp-tools', rev='1.5.3')
      .intransitive()
      .with_sources(),
    jar(org='net.sf.jwordnet', name='jwnl', rev='1.3.3')
      .intransitive()
      .with_sources(),
])
