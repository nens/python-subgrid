"""Utilities. For the moment documentation-generation related."""
from __future__ import print_function
import os


FUNCTIONS_HEADER = """
Wrapped Fortran subgrid library functions
-----------------------------------------

"""

FUNCTION_TEMPLATE = """
.. function:: {name}({args})

    Returns {result}

"""


def generate_functions_documentation():
    """Script to generate documentation on the wrapped Fortran functions.

    This function is installed via a setuptools console script entry point as
    a script with the same name.

    """
    # Assumption: we're called from the root fo the project.
    target_dir = './doc/source/'
    if not os.path.exists(target_dir):
        raise RuntimeError("Target dir %s doesn't exist." % target_dir)
    # Local import, utils is bound to importered, itself, too.
    out = ''
    from python_subgrid.wrapper import FUNCTIONS
    out += FUNCTIONS_HEADER
    for function in FUNCTIONS:
        args = ', '.join([arg.__class__.__name__ for arg in function['argtypes']])
        out += FUNCTION_TEMPLATE.format(
            name=function['name'],
            args=args,
            result=function['restype'].__class__.__name__)

    filename = os.path.join(target_dir, 'fortran_functions.rst')
    open(filename, 'w').write(out)
    print("Wrote fortran functions to %s" % filename)
