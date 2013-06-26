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


Mostly-standard compilation of the Fortran library on Ubuntu
------------------------------------------------------------

For the python wrapper we of course need the actual subgrid Fortran
library so that we can wrap it. A mostly standard installation on
ubuntu (which is also used on the jenkins test server and on the demo
website) uses the standard ubuntu netcdf packages and fortran::

    $ sudo apt-get install libnetcdf-dev libnetcdf6 gfortran

For the python netcdf library compilation we need another package::

    $ sudo apt-get install libhdf5-serial-dev

And we use the regular configure/make/make install steps with two changes::

    $ ./autogen.sh  # Try it without. If something breaks, run it.
    $ FCFLAGS="-I/usr/include" ./configure --prefix=/opt/3di
    $ make
    $ make install

The two changes:

- ``FCFLAGS`` to let fortran find the ubuntu netcdf packages.

- A ``--prefix`` to install it into ``/opt/3di/``.


Usage
-----

There are two ways to use the wrapper. A handy way is as a context
manager, so with a ``with`` statement::

    with SubgridWrapper(mdu='/full/path/model.mdu') as subgrid:
        # subgrid is the actual fortran library.
        subgrid.something()

The second way is by calling :meth:`start` and :meth:`stop` yourself and
using the :attr:`library` attribute to access the Fortran library::

    wrapper = SubgridWrapper(mdu='/full/path/model.mdu')
    wrapper.start()
    wrapper.library.something()
    ...
    wrapper.stop()

Note: Without the ``mdu`` argument, no model is loaded and you're free to
use the library as you want.


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


Test cases
----------

N&S is preparing model test cases ("model unit tests"), testing
individual bits and pieces of functionality. It works on linux only at
the moment, but that's just because it expects an
``/opt/3di/bin/subgridf90`` binary (so that's fixable).

It also requires a mercurial (``hg``) to be installed.

Run ``./update_testbank.sh`` to get the current set of test cases in
the ``testbank/`` subdirectory. (You might need to enable the
largefile mercurial extension in your ``~/.hgrc``). After that::

    $ bin/verify testbank

This generates some html files into the current directory. The html
output is also generated on jenkins:
http://jenkins.3di.lizard.net/testresults/ .
