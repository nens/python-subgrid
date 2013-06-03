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
