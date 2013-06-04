Changelog of python-subgrid
===================================================


0.2 (unreleased)
----------------

- The fortran library is loaded through a "with" context manager now. The
  previous version loaded it upon importing the ``wrapper.py`` file, handling
  everything on the main module level.

  The current approach is cleaner and takes care of startup/shutdown code and
  model initialization/cleanup automatically. The latter depends on the
  fortran code to function well, which at the moment is not the case yet.


0.1 (2013-06-04)
----------------

- Refactored the wrapper to make the code cleaner and more testable.

- If the models aren't available, the functional model tests are skipped. This
  makes for quicker tests if you want to test just the internal unittests.

- Modified library loading routine to automatically look in a couple of
  standard locations, amongst them ``/opt/3di/``.

- Added code from the previous ``python_wrapper`` directory.

- Initial project structure created with nensskel 1.33.dev0.
