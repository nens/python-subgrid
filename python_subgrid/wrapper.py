"""
This module provides a ctypes wrapper around the fortran 'subgrid' library.

"""
from __future__ import print_function
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
SHAPEARRAY = ndpointer(dtype='int32',
                       ndim=1,
                       shape=(MAXDIMS,),
                       flags='F')
FUNCTIONS = [
    {
        'name': 'update',
        'argtypes': [ctypes.c_double],
        'restype': ctypes.c_int,
    },
    {
        'name': 'getwaterlevel',
        'argtypes': [ctypes.POINTER(ctypes.c_double)] * 3,
        'restype': ctypes.c_int,
    },
    {
        'name': 'changebathy',
        'argtypes': [ctypes.c_double] * 5,
        'restype': ctypes.c_int,
    },
    {
        'name': 'discharge',
        'argtypes': [ctypes.POINTER(ctypes.c_double),
                     ctypes.POINTER(ctypes.c_double),
                     ctypes.c_char_p,
                     ctypes.POINTER(ctypes.c_int),
                     ctypes.POINTER(ctypes.c_double)],
        'restype': ctypes.c_int,
    },
    {
        'name': 'dropinstantrain',
        'argtypes': [ctypes.POINTER(ctypes.c_double)] * 4,
        'restype': ctypes.c_int
    },
    {
        'name': 'get_var_rank',
        'argtypes': [ctypes.c_char_p,
                     ctypes.POINTER(ctypes.c_int)],
        'restype': None,
    },
    {
        'name': 'get_var_shape',
        'argtypes': [ctypes.c_char_p,
                     SHAPEARRAY],
        'restype': None,  # Subroutine (no return type)
    },
    {
        'name': 'get_var_type',
        'argtypes': [ctypes.c_char_p,
                     ctypes.c_char_p],
        'restype': None,  # subroutine
    },
    {
        'name': 'loadmodel',
        'argtypes': [ctypes.c_char_p],
        'restype': ctypes.c_int,
    },
]
# TODO
# subgrid.get_0d_double.argtypes = [POINTER(c_double)]
# subgrid.get_0d_double.restype = None


def get_nd(subgrid, name):
    shape = np.empty((MAXDIMS, ), dtype='int32', order='fortran')
    name = ctypes.create_string_buffer(name)
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
    get_nd_type_.argtypes = [ctypes.c_char_p, ctypes.POINTER(arraytype)]
    get_nd_type_.restype = None
    # Get the array
    get_nd_type_(name, ctypes.byref(data))
    array = np.asarray(data)
    # Not sure why we need this....
    array = np.reshape(array.ravel(), shape, order='F')
    return array


class SubgridWrapper(object):
    """Context manager that provides the actual ctypes subgrid wrapper.

    The regular way to use it is with a ``with`` statement::

        with SubgridWrapper(mdu='/full/path/model.mdu') as subgrid:
            subgrid.something()

    Without the ``mdu`` argument, no model is loaded and you're free to use
    the library as you want.

    """

    def __init__(self, mdu=None):
        """Initialize the class.

        The ``mdu`` argument should be the path to a model's ``*.mdu``
        file.

        Nothing much should happen here so that the code remains easy to
        test. Most of the library-related initialization happens in the
        :method:`__enter__` method.
        """
        self.mdu = mdu
        self.original_dir = os.getcwd()

    def _libname(self):
        """Return platform-specific subgridf90 shared library name."""
        suffix = '.so'
        if platform.system() == 'Darwin':
            suffix = '.dylib'
        if platform.system() == 'Windows':
            suffix = '.dll'
        return 'libsubgrid' + suffix

    def _library_path(self):
        """Return full path to subgridf90 shared library.

        A couple of regular unix paths like ``/usr/lib/`` is searched by
        default. If your library is not in one of those, set a
        ``SUBGRID_PATH`` environement variable to the directory with your
        shared library.

        If the library cannot be found, a ``RuntimeError`` with debug
        information is raised.
        """
        known_paths = ['/usr/lib', '/usr/local/lib',
                       '/opt/3di/lib', '~/local/lib']
        # ^^^ Do not add your own path here!
        lib_path_from_environment = os.environ.get('SUBGRID_PATH', '')
        if lib_path_from_environment:
            known_paths[0:0] = [lib_path_from_environment]
        known_paths = [os.path.expanduser(path) for path in known_paths]
        possible_libraries = [os.path.join(path, self._libname())
                              for path in known_paths]
        for library in possible_libraries:
            if os.path.exists(library):
                logging.info("Using subgrid fortran library %s", library)
                return library
        msg = "Library not found, looked in %s" % ', '.join(possible_libraries)
        raise RuntimeError(msg)

    def _load_library(self):
        """Return the fortran library, loaded with ctypes."""
        return ctypes.cdll.LoadLibrary(self._library_path())

    def _annotate_functions(self):
        for function in FUNCTIONS:
            api_function = getattr(self.library, function['name'])
            api_function.argtypes = function['argtypes']
            api_function.restype = function['restype']
        self.library.get_nd = functools.partial(get_nd, subgrid=self.library)

    def _load_model(self):
        os.chdir(os.path.dirname(self.mdu))
        exit_code = self.library.loadmodel(self.mdu)
        if exit_code:
            msg = "Loading model {mdu} failed with exit code {code}"
            raise RuntimeError(msg.format(mdu=self.mdu, code=exit_code))

    def __enter__(self):
        self.library = self._load_library()
        self._annotate_functions()
        self.library.startup()  # Fortran init function.
        if self.mdu:
            self._load_model()
        return self.library

    def __exit__(self, type, value, tb):
        if self.mdu:
            self.library.finalizemodel()
        self.library.shutdown()  # Fortran cleanup function.
        # del self.library  # This one doesn't work.
        os.chdir(self.original_dir)
