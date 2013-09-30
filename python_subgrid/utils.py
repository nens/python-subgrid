"""Utilities. For the moment documentation-generation related."""
from __future__ import print_function
import collections
import ctypes
import logging
import os
import platform

SUFFIXES = collections.defaultdict(lambda: '.so')
SUFFIXES['Darwin'] = '.dylib'
SUFFIXES['Windows'] = '.dll'
SUFFIX = SUFFIXES[platform.system()]


class NotDocumentedError(Exception):
    pass


# Utility functions for library unloading
def isloaded(lib):
    """return true if library is loaded"""
    libp = os.path.abspath(lib)
    # posix check to see if library is loaded
    ret = os.system("lsof -p %d | grep %s > /dev/null" % (os.getpid(), libp))
    return (ret == 0)


def dlclose(lib):
    """force unload of the library"""
    handle = lib._handle
    # this only works on posix I think....
    # windows should use something like:
    # http://msdn.microsoft.com/en-us/library/windows/desktop/ms683152(v=vs.85).aspx # pep8: disable-msg=W0501
    name = 'libdl' + SUFFIX[platform.system()]
    libdl = ctypes.cdll.LoadLibrary(name)
    libdl.dlerror.restype = ctypes.c_char_p
    libdl.dlclose.argtypes = [ctypes.c_void_p]
    logging.debug('Closing dll (%x)', handle)
    rc = libdl.dlclose(handle)
    if rc != 0:
        logging.debug('Closing failed, looking up error message')
        error = libdl.dlerror()
        logging.debug('Closing dll returned %s (%s)', rc, error)
        if error == 'invalid handle passed to dlclose()':
            raise ValueError(error)
    else:
        logging.debug('Closed')


FILE_HEADER = """
Fortran functions and variables
===============================

"""


FUNCTIONS_HEADER = """
Wrapped Fortran subgrid library functions
-----------------------------------------

"""

FUNCTION_TEMPLATE = """
.. function:: {name}({args})

    Returns {result}

"""

VARIABLES_HEADER = """
Directly accessible Fortran variables
-------------------------------------

These variables can be called from the wrapper's ``get_nd`` function.

"""

VARIABLE_TEMPLATE = """
.. attribute:: {name}

    {description}

"""


def generate_functions_documentation():
    """Script to generate documentation on the wrapped Fortran functions.

    This function is installed via a setuptools console script entry point as
    a script with the same name.

    """
    # Assumption: we're called from the root of the project.
    target_dir = './doc/source/'
    assert os.path.exists(target_dir), "Target dir %s doesn't exist." % target_dir
    # Local import, utils is bound to importered, itself, too.
    out = ''
    out += FILE_HEADER

    from python_subgrid.wrapper import FUNCTIONS
    out += FUNCTIONS_HEADER
    for function in FUNCTIONS:
        args = ', '.join([arg.__class__.__name__ for arg in function['argtypes']])
        out += FUNCTION_TEMPLATE.format(
            name=function['name'],
            args=args,
            result=function['restype'].__class__.__name__)

    from python_subgrid.wrapper import DOCUMENTED_VARIABLES
    out += VARIABLES_HEADER
    for variable in sorted(DOCUMENTED_VARIABLES.keys()):
        out += VARIABLE_TEMPLATE.format(
            name=variable,
            description=DOCUMENTED_VARIABLES[variable])

    filename = os.path.join(target_dir, 'fortran_functions.rst')
    open(filename, 'w').write(out)
    print("Wrote fortran functions to %s" % filename)
