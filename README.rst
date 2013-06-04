Python wrapper for the 3di subgrid library
==========================================

Setup
-----

We need the compiled Fortran subgrid library. There are a couple of common
locations (like ``/usr/lib/``) where we look for it.

A convention on linux is to install the library into ``/opt/3di/``. This
lcoation is found by default, too.

In case you have an alternative location, you can set the ``SUBGRID_PATH``
environment variable::

   $ export SUBGRID_PATH=/home/user/svn/3di/trunk/subgridf90/src/.libs

(On windows the command is ``set`` instead of ``export``).

Usage
-----

The library is loaded with a context manager::

    >>> from python_subgrid.wrapper import SubgridWrapper
    >>> with SubgridWrapper() as subgrid:
    ...     # subgrid is the actual fortran library.
    ...     subgrid.something()

Most often you want to load a model. All the model initialization/teardown is
handled for you, including changing directory to the model's directory (and
back afterwards). Just pass the full path to the ``*.mdu`` file::

    >>> with SubgridWrapper(mdu='/full/path/model.mdu') as subgrid:
    ...     subgrid.something()


Automatic tests
---------------

The code is tested on http://jenkins.3di.lizard.net. The ``libsubgrid.so``
that is used there is the one from the last successful build of
``subgridf90``, which is placed in ``/opt/3di/``.

The tests need testcases. Currently it are some of the actual in-production
datasets used for the 3di websites ("betondorp", "delfland"). These are
available as svn:externals in the subgrid library directory.

You can symlink those directories next to this README. You can also set
the ``SCENARIO_BASEDIR`` environment variable. Either set it globally or run
the tests like this, for instance::

    $ SCENARIO_BASEDIR=../subgridf90/testcases bin/test

If the scenarios cannot be found, the functional model tests are skipped, btw.
