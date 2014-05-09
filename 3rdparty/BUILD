# ==================================================================================================
# Copyright 2011 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================

# This BUILD file defines common external library dependencies used across many modules. Modules
# can use these jar_library deps by specifying pants('3rdparty:[name]') in their dependencies list.

###################
# Production libs
#

jar_library(name = 'aopalliance',
            dependencies = [
              jar(org = 'aopalliance', name = 'aopalliance', rev = '1.0').with_sources()
            ]
          )

jar_library(name = 'args4j',
            dependencies = [ jar(org = 'args4j', name = 'args4j', rev = '2.0.16').with_sources() ])

jar_library(name = 'commons-codec',
            dependencies = [
              jar(org = 'commons-codec', name = 'commons-codec', rev = '1.6').with_sources()
            ]
           )

jar_library(name = 'commons-io',
            dependencies = [
              jar(org = 'commons-io', name = 'commons-io', rev = '2.1').with_sources()
            ]
           )

jar_library(name = 'commons-lang',
            dependencies = [
              jar(org = 'commons-lang', name = 'commons-lang', rev = '2.6').with_sources()
            ]
           )

jar_library(name = 'gson',
            dependencies = [
              jar(org = 'com.google.code.gson', name = 'gson', rev = '2.2.2').with_sources()
            ])

jar_library(name = 'guice',
            dependencies = [
              jar(
                org = 'com.google.inject', name = 'guice', rev = '3.0',
                apidocs = 'http://google-guice.googlecode.com/svn/tags/3.0/javadoc/'
              ).with_sources()
            ]
           )

jar_library(name = 'guice-multibindings',
            dependencies = [
              jar(org = 'com.google.inject.extensions', name = 'guice-multibindings', rev = '3.0')
                .with_sources()
            ]
           )

jar_library(name = 'guice-servlet',
            dependencies = [
              jar(org = 'com.google.inject.extensions', name = 'guice-servlet', rev = '3.0')
                .with_sources()
            ]
           )

jar_library(name = 'jetty',
            dependencies = [
              jar(org = 'org.mortbay.jetty', name = 'jetty', rev = '6.1.25').with_sources()
            ]
           )

jar_library(name = 'joda-time',
            dependencies = [
              jar(org = 'joda-time', name = 'joda-time', rev = '2.3'),
              jar(org = 'org.joda', name = 'joda-convert', rev = '1.5')
            ]
           )

# Extract from the jsr166e proposal
# See http://github.com/twitter/jsr166e
jar_library(name = 'jsr166e',
            dependencies = [
              jar(org = 'com.twitter', name = 'jsr166e', rev = '1.0.0').with_sources()
            ]
           )

jar_library(name = 'log4j',
            dependencies = [ jar(org = 'log4j', name = 'log4j', rev = '1.2.15').with_sources() ])

jar_library(name = 'ostrich',
            dependencies = [
              jar(org = 'com.twitter', name = 'ostrich', rev = '9.1.2').with_sources()
            ])

jar_library(name = 'protobuf-2.4.1',
            dependencies = [
              jar(org = 'com.google.protobuf', name = 'protobuf-java', rev = '2.4.1').with_sources()
            ]
           )

jar_library(name = 'protobuf-java',
            dependencies = [ pants(':protobuf-2.4.1') ])

jar_library(name = 'scala-compiler',
            dependencies = [
              jar(org='org.scala-lang', name='scala-compiler', rev='2.9.3').with_sources()
            ]
           )

jar_library(name = 'scala-library',
            dependencies = [
              jar(org='org.scala-lang', name='scala-library', rev='2.9.3').with_sources()
            ]
           )

jar_library(name = 'scalatest',
            dependencies = [
              jar(org='org.scalatest', name='scalatest_2.9.2', rev='1.9.1').with_sources()
            ]
           )

jar_library(name = 'servlet-api',
            dependencies = [
              jar(org = 'javax.servlet', name = 'servlet-api', rev = '2.5').with_sources()
            ]
           )

SLF4J_VERSION = '1.6.1'

jar_library(name = 'slf4j-api',
            dependencies = [
              jar(org = 'org.slf4j', name = 'slf4j-api', rev = SLF4J_VERSION).with_sources()
            ]
           )

jar_library(name = 'slf4j-jdk14',
            dependencies = [
              jar(org = 'org.slf4j', name = 'slf4j-jdk14', rev = SLF4J_VERSION).with_sources()
            ]
           )

jar_library(name = 'spy-memcached',
            dependencies = [
              jar(org = 'spy', name = 'spymemcached', rev = '2.8.1').with_sources()
            ]
           )

jar_library(name = 'stringtemplate',
            dependencies = [
              jar(org = 'org.antlr', name = 'stringtemplate', rev = '3.2.1').with_sources()
            ]
           )

jar_library(name = 'libthrift-0.5.0',
            dependencies = [
              jar(org = 'org.apache.thrift', name = 'libthrift', rev = '0.5.0-1').with_sources(),
            ]
           )

jar_library(name = 'thrift-0.5.0',
            dependencies = [
              pants(':commons-lang'),
              pants(':libthrift-0.5.0'),
              pants(':slf4j-api'),

              # TODO(John Sirois): Find a sane way to have thrift dependees who do not themselves
              # use slf4j get a concrete binding.
              pants(':slf4j-jdk14'),
            ]
           )

jar_library(name = 'thrift-0.5.0-finagle',
            dependencies = [
              pants(':thrift-0.5.0'),

              # finagle thrift extra deps
              pants('3rdparty/jvm/com/twitter:finagle-core'),
              pants('3rdparty/jvm/com/twitter:finagle-thrift'),
              pants('3rdparty/jvm/com/twitter:util-core'),
            ]
           )

jar_library(name = 'thrift',
            dependencies = [ pants(':thrift-0.5.0') ])

jar_library(name = 'twitter-text',
            dependencies = [ jar(org = 'com.twitter', name = 'twitter-text', rev = '1.5.0') ])

jar_library(name = 'twitter-config-yaml',
            dependencies = [
              jar(org = 'com.twitter', name = 'twitter-config-yaml', rev = '1.2.0').with_sources()
            ])

jar_library(name = 'zookeeper',
            dependencies = [
              jar(org = 'org.apache.zookeeper', name = 'zookeeper', rev = '3.3.4').with_sources()
                .exclude(org = 'jline', name = 'jline')
                .exclude(org = 'javax.jms', name = 'jms')
                .exclude(org = 'com.sun.jdmk', name = 'jmxtools')
                .exclude(org = 'com.sun.jmx', name = 'jmxri')
            ]
           )

###############
# Test support
#

jar_library(name = 'easymock',
            dependencies = [
              jar(org = 'org.easymock', name = 'easymock', rev = '3.2').with_sources(),
              # Class extension is needed to support the old version of easymockclassextension that
              # is not dependend on by the easymock dependency
              jar(org = 'org.easymock', name = 'easymockclassextension', rev = '3.2').with_sources(),
            ]
           )

jar_library(name = 'mockito',
            dependencies = [
              jar(org = 'org.mockito', name = 'mockito-all', rev = '1.9.0').with_sources()
            ]
           )

jar_library(name = 'hamcrest-core',
            dependencies = [ jar(org = 'org.hamcrest', name = 'hamcrest-core', rev = '1.2') ])

jar_library(name = 'junit',
            dependencies = [
              jar(org = 'junit', name = 'junit-dep', rev = '4.10').with_sources(),
              pants(':hamcrest-core'),
            ]
           )

jar_library(name = 'specs_2.9',
            dependencies = [
              jar(org = 'org.scala-tools.testing', name = 'specs_2.9.3', rev = '1.6.9')
            ]
           )

jar_library(name = 'specs', dependencies = [ pants(':specs_2.9') ])

jar_library(name = 'tl4j',
            dependencies = [
              jar(org = 'com.google.testing', name = 'test-libraries-for-java', rev = '1.1.1')
                # tl4j by default pulls in junit-4.6, which conflicts with 4.10 needed by our
                # testing code (e.g. ConcurrentJunitRunner). So exclude it here so that the junit
                # target defined above is used instead. tl4j seems to be happy with junit-4.10.
                .exclude(org = 'junit', name='junit')
            ]
           )

###############
# Benchmark support
#
jar_library(name = 'caliper',
            dependencies = [
              # Warning: keep the library version aligned with
              # build-support/profiles/benchmark-caliper-0.5-ivy.xml
              jar(org = 'com.google.caliper', name = 'caliper', rev = '0.5-rc1').with_sources(),
            ]
           )
