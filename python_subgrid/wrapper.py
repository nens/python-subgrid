from __future__ import print_function
from ctypes import POINTER, create_string_buffer, byref, c_int, c_char_p
import ctypes
import functools
import logging
import os
import platform

from numpy.ctypeslib import ndpointer
import numpy as np


MAXDIMS = 6
TYPEMAP = {
    "int": "int32",
    "double": "double",
    "float": "float32"
}


def _libname():
    """Return platform-specific subgridf90 shared library name."""
    suffix = '.so'
    if platform.system() == 'Darwin':
        suffix = '.dylib'
    if platform.system() == 'Windows':
        suffix = '.dll'
    return 'libsubgrid' + suffix


def _library_path():
    """Return full path to subgridf90 shared library."""
    known_paths = ['/usr/lib', '/usr/local/lib',
                   '/opt/3di/lib', '~/local/lib']
    # ^^^ Do not add your own path here!
    lib_path_from_environment = os.environ.get('SUBGRID_PATH', '')
    if lib_path_from_environment:
        known_paths[0:0] = [lib_path_from_environment]
    known_paths = [os.path.expanduser(path) for path in known_paths]
    possible_libraries = [os.path.join(path, _libname())
                          for path in known_paths]
    for library in possible_libraries:
        if os.path.exists(library):
            logging.info("Using subgrid fortran library %s", library)
            return library
    msg = "Library not found, looked in %s" % ', '.join(possible_libraries)
    raise RuntimeError(msg)


subgrid = ctypes.cdll.LoadLibrary(_library_path())

subgrid.update.argtypes = [ctypes.c_double]
subgrid.update.restype = ctypes.c_int

subgrid.getwaterlevel.argtypes = [ctypes.POINTER(ctypes.c_double)] * 3
subgrid.getwaterlevel.restype = ctypes.c_int

arraytype1 = ndpointer(dtype='double',
                       ndim=3,
                       shape=(2, 3, 4),
                       flags='F')
subgrid.subgrid_arraypointer.argtypes = [ctypes.POINTER(arraytype1)]
subgrid.subgrid_arraypointer.restype = None

subgrid.changebathy.argtypes = [ctypes.c_double] * 5
subgrid.changebathy.restype = ctypes.c_int

subgrid.discharge.argtypes = [ctypes.POINTER(ctypes.c_double),
                              ctypes.POINTER(ctypes.c_double),
                              c_char_p,
                              ctypes.POINTER(ctypes.c_int),
                              ctypes.POINTER(ctypes.c_double)]
subgrid.discharge.restype = ctypes.c_int

# TODO
# subgrid.get_0d_double.argtypes = [POINTER(c_double)]
# subgrid.get_0d_double.restype = None

subgrid.get_var_rank.argtypes = [c_char_p, POINTER(c_int)]
subgrid.get_var_rank.restype = None

arraytype2 = ndpointer(dtype='int32',
                       ndim=1,
                       shape=(MAXDIMS,),
                       flags='F')
shape = np.empty((MAXDIMS, ), dtype='int32', order='fortran')
subgrid.get_var_shape.argtypes = [c_char_p, arraytype2]
subgrid.get_var_type.argtypes = [c_char_p, c_char_p]


def get_nd(subgrid, name):
    name = create_string_buffer(name)
    rank = subgrid.get_var_rank(name)
    shape = subgrid.get_var_shape(name)
    type_ = subgrid.get_var_type(name)

    arraytype = ndpointer(dtype=TYPEMAP[type_],
                          ndim=rank,
                          shape=shape[::-1],
                          flags='F')
    # Create a pointer to the array type
    data = arraytype()
    get_nd_type_ = getattr(subgrid, 'get_nd'.format(rank=rank, type=type_))
    get_nd_type_.argtypes = [c_char_p, POINTER(arraytype)]
    get_nd_type_.restype = None
    # Get the array
    get_nd_type_(name, byref(data))
    array = np.asarray(data)
    # Not sure why we need this....
    array = np.reshape(array.ravel(), shape, order='F')
    return array

subgrid.get_nd = functools.partial(get_nd, subgrid=subgrid)
