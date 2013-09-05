3Di library roadmap
===================

.. note::

   This is a short explanatory document. It should fit on one A4 when
   printed. It should rarely change.


End goal
--------

- Pure Python library. Note that this is mostly a driving direction,
  the actual core calculation will remain in Fortran.

- Handy, usable library. Note: library and not framework or product,
  so it is meant to be called, it won't do anything of itself.

- Object oriented instead of simply calling functions and using global
  memory structures.

- Extendable/adjustable so that the library can stay focused.

- 100% tested and documented.

- Open source. Note that this isn't attainable yet, but technically it
  should be possible. And it forces us to look hard at extendability:
  proprietary functionality should be pluggable.


Structure
---------

The basic structure is in three parts:

- **Fortran code**: separate functions and separate memory structures.

- **Direct wrapper**: pretty straightforward Python+ctypes wrapper of
  the Fortran functions and memory structures. Numpy and Pandas are
  used.

- **Object oriented mapper**: friendly wrapper of the functions and
  memory structures to meaningful objects ("calculation", "grid",
  "calculation step" and so on). Here's where the
  extendability/adjustability also plays out.


How to get there?
-----------------

The main idea is **iterative development**. We already have something
that's working, so we can iteratively improve and extend it. 

- We are already using the library, so those programs can dictate the
  priorities.

- Incrementally move functionality from Fortran to Python.
  Specific Fortran functions can be better handled by specific Python
  objects that call generic Fortran functionality. Slowly take over
  management tasks like configuring and starting up the calculation
  core, for instance.

- Make sure there's a good overview of all available Fortran
  functionality and how/if that's used by the Python objects. This
  shows what has been done and what can be done still.
