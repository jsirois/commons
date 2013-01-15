**Note**: This documentation is written during a transitional period for
pants.  If you're looking to migrate your projects from old pants to
pants.new there are a few
[[steps to follow|pants('src/python/twitter/pants/docs:migration')]] to get
your BUILD files in order.

# What is Pants?

Pants is a build tool. It is similar in some regards to make, maven,
ant, gradle, sbt, etc. However, pants differs in some important
design goals. Pants optimizes for

* building multiple, dependent projects from source
* building projects in a variety of languages
* speed of build execution

BUILD files define _build targets_. A build target might produce some output
file[s]; it might have sources and/or depend on other build targets.
There might be several BUILD files dotted all over the codebase; a target in
one can depend on a target in another.

Pants reads BUILD files, computes the dependency graph of build targets,
and executes a specified set of goals against those targets, where goals
are actions like `test` or `compile`.

A Pants build "sees" only the target it's building and the transitive
dependencies of that target. It doesn't attempt to build entire source trees.
This approach works well for a big repository containing several projects,
where a tool that insists on building everything would bog down.

This guide explains how to author BUILD files and how to use the Pants tool.

# Installing and Troubleshooting Pants Installations

See [[installation instructions|pants('src/python/twitter/pants:install')]].

# Using Pants

Pants is invoked via the `pants` script, usually located in the root of
your source repository. When you invoke pants, you specify one or more
goals, one or more targets to run those goals against, and zero or
more command line options.

A pants command line has the general form

    pants goal <goal(s)> <target(s)> <option(s)>

Options don't need to be at the end. These both work:

    pants goal compile --compile-scalac-warnings test src/scala/myproject
    pants goal compile test src/scala/myproject --compile-scalac-warnings

To see a goal's configuration flags, use the --help option, e.g.

    pants goal compile --help

**Listing Goals:** The `goal` command is an intermediate artifact of the
migration from "pants.old" to "pants.new". In the near future, the `goal`
command will disappear.

Running `pants goal` lists all installed goals:

    [local ~/projects/science]$ ./pants goal
    Installed goals:
          binary: Create a jvm binary jar.
          bundle: Create an application bundle from binary targets.
      checkstyle: Run checkstyle against java source code.
      ......

Goals may depend on each other. For example, `compile` depends on `resolve`,
so running `compile` will resolve any unresolved jar dependencies via `ivy`.

## Targets, Goals, Products

As a pants user, you want to know these concepts:

* A _target_ specifies something that exists in or should be produced by
  the build: source files, documentation, libraries, ... These are the
  "nouns" of your build.
* A _goal_ specifies a high-level action to take on targets: compile,
  test, ... These are the "verbs" of your build.
* A _product_ is the output of a goal: `.class` files, `.jar` files,
  generated source files, ...

## A Simple BUILD file

A BUILD file defines targets and dependencies. `pants` uses the Python
interpreter to parse the BUILD files; thus, they look a lot like Python
constructors with kwargs and can be augmented with Python code as needed.
A BUILD file may contain multiple build targets.

### Library Dependencies

Here's a (fake) example of a single build target:

    :::python
    scala_library(
      name = 'util',
      dependencies = [pants('3rdparty:commons-math'),
                      pants('3rdparty:thrift'),
                      pants('core/src/main/scala/com/foursquare/auth'),
                      pants(':base')],
      sources = rglobs('*.scala'),
    )

* A target's type (here, `scala_library`) determines what
  actions, if any, build it: which compilers to invoke and
  so on. Pants also supports java\_library and python_library.
* We refer to targets by the BUILD file's path plus the target name,
  which therefore must be unique within its BUILD file.
  In this case the build target is named `util`. If it's in
  `core/src/main/scala/com/foursquare/base/BUILD`, its fully-qualified name is
  `core/src/main/scala/com/foursquare/base/BUILD:util`.
* The target's dependencies are expressed as a list of other build targets,
  each wrapped by the invocation `pants()`. The dependency on
  `pants('core/src/main/scala/com/foursquare/auth')` has no `:<name>`
  suffix. This uses a shorthand: if a
  target's name is the same as its BUILD file's directory, you
  can omit the name. So this dependency is short for
  `pants('core/src/main/scala/com/foursquare/auth/BUILD:auth')`. The
  `pants(':base')` dependency is shorthand for "the target named
  'base' in this BUILD file."
* The sources are expressed as a list of file paths relative to the
  BUILD file's directory. In most cases, it's not convenient to enumerate
  the files explicitly, so you can specify them with `globs(<file
  pattern>)`, which matches in the BUILD file's directory, or
  `rglobs(<file pattern>)`, which matches the subtree rooted at
  the BUILD file. Each of these glob functions returns a list
  of file paths, so you can Pythonically add or remove files.
  E.g., `globs('*Foo.scala', '*Bar.scala') + ['Baz.scala']` or
  `[f for f in globs('*.scala') if not f in globs('*-test.scala')]`
* If BUILD files specify a cycle, Pants detects it and errors out
  (actually, it doesn't currently due to a bug, but that will be fixed soon).

### External Dependencies

Not everything's source code is in your repository.
By convention, we keep build information about external libraries in a
directory tree whose root is called `3rdparty.`

*Java Jars*

    :::python
    jar_library(name='jackson',
      dependencies=[
        jar(org='org.codehaus.jackson', name='jackson-core-asl', rev='1.8.8').withSources(),
        jar(org='org.codehaus.jackson', name='jackson-mapper-asl', rev='1.8.8').withSources(),
        jar(org='org.codehaus.jackson', name='jackson-xc', rev='1.8.8').withSources()
      ]
    )

The target name is a convenient alias for an external
jar (or, as in this example, multiple jars). These `jar`
targets have no `sources` argument, but instead the
information `ivy` uses to fetch the jars.

*Python*

    :::python
    python_library(
      name='beautifulsoup',
      dependencies=[python_requirement('BeautifulSoup==3.2.0')]
    )
    python_library(
      name='markdown',
      dependencies=[python_requirement('markdown')]
    )

The target name is a convenient alias. The `dependencies` is a list of one
or more `python_requirement` targets. The `python_requirement` can refer
to a `pkg_resources`
[requirements string](http://packages.python.org/distribute/pkg_resources.html#requirements-parsing).
Pants looks in a few places for Python `.egg`s as configured in your
`python.ini` file's `python-repos` section.

To use the external Python module, another python target could have a
dependency:

    :::python
    python_binary(name = 'mach_turtle',
      source = 'mach_turtle.py',
      dependencies = [pants('3rdparty/python:beautifulsoup')]
    )

...and the Python script's import would look like

    :::python
    from BeautifulSoup import BeautifulSoup

## pants.ini

Pants is intended to be used in a wide variety of source repositories,
and as such is highly customizable via a `pants.ini` file located in the
root of your source repository. You can modify a broad range of
settings here, including specific binaries to use in your toolchain,
arguments to pass to tools, etc.

# Common Tasks

**Compiling**

    pants goal compile src/java/yourproject

**Running Tests**

    pants goal test test/java/yourproject

**Packaging Binaries**

To create a jar containing just the code built by a target, use the
`jar` goal:

    pants goal jar src/java/yourproject

To deploy a "fat" jar that contains code for a `jvm_binary` target and its
dependencies, use the `binary` goal and the `--binary-deployjar` flag:

    pants goal binary --binary-deployjar src/java/yourproject

**Invalidation**

The `invalidate` goal clears pants' internal state.

    pants goal invalidate compile src/java/yourproject

invalidates pants' caches. In most cases, this forces a clean build.

**Cleaning Up**

The `clean-all` goal does a more vigorous cleaning of pants' state.

    pants goal clean-all

Actually removes the pants workdir, and kills any background processes
used by pants in the current repository.

**Publishing**

TODO: this

**Adding jar dependencies**

TODO: this

**Generating Source**

TODO: this

# Built-In Targets

TODO: add a brief description and example of each target.

## annotation_processor

## exclude

## jar

## jar_library

## java_library

## java\_protobuf_library

## java_tests

## java\_thrift_library

## jvm_binary

## page

## pants

## python\_antlr_library

## python_binary

## python_requirement

## python_tests

## python\_thrift_library

## repository

## scala_library

## scala_tests

## sources

# Extending BUILD files with goals

TODO: add description, examples of extensions

# Pants Internals

TODO: this

## .pants.d

## BUILD file parsing

## ivy resolution

## hashing

## task batching

## product mapping
=======

## Credits

Pants was originally written by John Sirois.

Major contributors in alphabetical order:

- Alec Thomas
- Benjy Weinberger
- Bill Farner
- Brian Wickman
- David Buchfuhrer
- John Sirois
- Mark McBride

If you are a contributor, please add your name to the list!
