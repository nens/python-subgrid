Wrapper API documentation
=========================

.. automodule:: python_subgrid.wrapper

The main item is the :class:`SubgridWrapper` which is a `context manager
<http://docs.python.org/2/reference/datamodel.html#context-managers>`_. Basically,
you use it with the ``with`` statement.

.. autoclass:: SubgridWrapper

.. automethod:: SubgridWrapper.__init__

.. automethod:: SubgridWrapper.start

.. automethod:: SubgridWrapper.stop


Context manager: ``with ... as ...``
------------------------------------

:class:`SubgridWrapper` is also usable as a handy `context manager
<http://docs.python.org/2/reference/datamodel.html#context-managers>`_. Basically,
you use it with the ``with`` statement.

When you enter and exit the ``with`` block, Python executes the
:meth:`SubgridWrapper.__enter__` and :meth:`SubgridWrapper.__exit__`
methods automatically. These two handle the startup and teardown of the
Fortran library and the model for you.

.. automethod:: SubgridWrapper.__enter__

.. automethod:: SubgridWrapper.__exit__


Fortran coupling via ctypes
---------------------------

We use `ctypes <http://docs.python.org/2/library/ctypes.html>`_ for loading
and talking to the Fortran library. Two methods interact with ctypes:

.. automethod:: SubgridWrapper._load_library

.. automethod:: SubgridWrapper._annotate_functions


Helper methods
--------------

There are a couple of helper methods that are used internally:

.. automethod:: SubgridWrapper._libname

.. automethod:: SubgridWrapper._library_path

.. automethod:: SubgridWrapper._load_model
