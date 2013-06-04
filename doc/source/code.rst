Wrapper API documentation
=========================

.. automodule:: python_subgrid.wrapper

The main item is the :class:`SubgridWrapper` which is a `context manager
<http://docs.python.org/2/reference/datamodel.html#context-managers>`_. Basically,
you use it with the ``with`` statement.

.. autoclass:: SubgridWrapper

There are a couple of helper methods that are used internally:

.. automethod:: SubgridWrapper._libname

.. automethod:: SubgridWrapper._library_path

.. automethod:: SubgridWrapper._load_library
