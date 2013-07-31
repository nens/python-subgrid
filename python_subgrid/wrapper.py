"""
This module provides a ctypes wrapper around the fortran 'subgrid' library.

"""

from __future__ import print_function
import functools
import logging
import os
import platform

# Let's keep these in the current namespace
# types
from ctypes import c_double, c_int, c_char_p, c_float, c_void_p
# for making strings
from ctypes import create_string_buffer
# pointering
from ctypes import POINTER, byref
# loading
from ctypes import cdll
# nd arrays
from numpy.ctypeslib import ndpointer

import numpy as np

import faulthandler
faulthandler.enable()


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

# If you make changes in FUNCTIONS, run
# 'bin/generate_functions_documentation' to re-generate the automatic
# documentation in ./doc/source/fortran_functions.rst.
FUNCTIONS = [
    {
        'name': 'update',
        'argtypes': [POINTER(c_double)],
        'restype': c_int,
    },
    {
        'name': 'startup',
        'argtypes': [],
        'restype': c_int,
    },
    {
        'name': 'shutdown',
        'argtypes': [],
        'restype': c_int,
    },
    {
        'name': 'loadmodel',
        'argtypes': [c_char_p],  # I think this is a pointer to a char_p
        'restype': c_int,
    },
    {
        'name': 'initmodel',
        'argtypes': [],
        'restype': c_int,
    },
    {
        'name': 'finalizemodel',
        'argtypes': [],
        'restype': c_int,
    },
    {
        'name': 'changebathy',
        'argtypes': [
            POINTER(c_double),  # xc
            POINTER(c_double),  # yc
            POINTER(c_double),  # size
            POINTER(c_double),  # bvalue
            POINTER(c_int)      # bmode
                 ],
        'restype': c_int,
    },
    {
        'name': 'floodfilling',
        'argtypes': [POINTER(c_double),
                     POINTER(c_double),
                     POINTER(c_double),
                     POINTER(c_int)],
        'restype': c_int,
    },
    {
        'name': 'discharge',
        'argtypes': [POINTER(c_double),
                     POINTER(c_double),
                     c_char_p,
                     POINTER(c_int),
                     POINTER(c_double)],
        'restype': c_int,
    },
    {
        'name': 'discard_manhole',
        'argtypes': [POINTER(c_double),
                     POINTER(c_double)],
        'restype': c_int,
    },
    {
        'name': 'dropinstantrain',
        'argtypes': [POINTER(c_double)] * 4,
        'restype': c_int
    },
    {
        'name': 'getwaterlevel',
        'argtypes': [POINTER(c_double)] * 3,
        'restype': c_int,
    },
    {
        'name': 'subgrid_info',
        'argtypes': [],
        'restype': None,
    },
]




class SubgridWrapper(object):
    """Wrapper around the ctypes-loaded Fortran subgrid library.

    There are two ways to use the wrapper. A handy way is as a context
    manager, so with a ``with`` statement::

        with SubgridWrapper(mdu='/full/path/model.mdu') as subgrid:
            # subgrid is the wrapper around library.
            subgrid.update(1.0)
            # or you can call the library explicitly
            subgrid.library.update(byref(c_double(1.0)))

    The second way is by calling :meth:`start` and :meth:`stop` yourself and
    using the :attr:`library` attribute to access the Fortran library::

        wrapper = SubgridWrapper(mdu='/full/path/model.mdu')
        wrapper.start()
        wrapper.update(1.0)
        # or if you want to pass pointers
        wrapper.library.update(byref(c_double(1.0)))
        ...
        wrapper.stop()

    Note: Without the ``mdu`` argument, no model is loaded and you're free to
    use the library as you want.

    """
    library = None

    # This should be the same as in the subgridapi
    MAXSTRLEN=1024
    MAXDIMS=6
    def __init__(self, mdu=None):
        """Initialize the class.

        The ``mdu`` argument should be the path to a model's ``*.mdu``
        file.

        Nothing much should happen here so that the code remains easy to
        test. Most of the library-related initialization happens in the
        :meth:`start` method.
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
                       '/opt/3di/lib', '~/local/lib',
                       '~/.local/lib', '.']
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
        """Return the fortran library, loaded with """
        return cdll.LoadLibrary(self._library_path())

    def _annotate_functions(self):
        """Help ctypes by telling it type information about Fortran functions.

        Functions in the loaded Fortran library are called through  The
        variables inside Fortran don't automatically translate to and from
        Python variables. We can help ctypes a lot by telling it about the
        argument types and return type(s) of the various functions.

        The annotations also make our own life easier as it allows ctypes to
        do a lot of type conversions automatically for us. We can pass most values
        without the need to convert to a pointer first.

        On the wrapper.library the functions can be called as ctypes functions.
        On the wrapper the functions can be called with python types.

        """
        def wrap(func):
            """wrap the function so we can do type conversion and sanity check"""
            @functools.wraps(func, assigned=('restype', 'argtypes'))
            def wrapped(*args):
                if len(args) != len(func.argtypes):
                    logging.warn("{} {} not of same length".format(args, func.argtypes))

                typed_args = []
                for (arg, argtype) in zip(args, func.argtypes):
                    if isinstance(argtype._type_, str):
                        # create a string buffer for strings
                        typed_arg = create_string_buffer(arg)
                    else:
                        # for other types, use the type to do the conversion
                        typed_arg = argtype(argtype._type_(arg))
                    typed_args.append(typed_arg)
                result = func(*typed_args)
                return result.contents if hasattr(result, 'contents') else result
            return wrapped
        for function in FUNCTIONS:
            api_function = getattr(self.library, function['name'])
            api_function.argtypes = function['argtypes']
            api_function.restype = function['restype']
            # decorate the function with type conversion,
            # so we can pass in normal python stuff
            # make sure the function properties are copied to the wrapper (normally copy __doc__ etc...)
            # @functools.wraps(api_function,assigned=('restype','argtypes') )
            f = wrap(api_function)
            assert hasattr(f, 'argtypes')
            setattr(self, function['name'], f)

    def _load_model(self):
        os.chdir(os.path.dirname(self.mdu))
        exit_code = self.library.loadmodel(self.mdu)
        if exit_code:
            msg = "Loading model {mdu} failed with exit code {code}"
            raise RuntimeError(msg.format(mdu=self.mdu, code=exit_code))

    def start(self):
        """Initialize and load the Fortran library (and model, if applicable).

        The Fortran library is loaded and ctypes is used to annotate functions
        inside the library. The Fortran library's initialization is called.

        Normally a path to an ``*.mdu`` model file is passed to the
        :meth:`__init__`. If so, that model is loaded. Note that
        :meth:`_load_model` changes the working directory to that of the model.

        """
        self.library = self._load_library()
        self._annotate_functions()
        self.library.startup()  # Fortran init function.
        if self.mdu:
            self._load_model()

    def stop(self):
        """Shutdown the library and clean up the model.

        Note that the Fortran library's cleanup code is not up to snuff yet,
        so the cleanup is not perfect. Note also that the working directory is
        changed back to the original one.

        """
        if self.mdu:
            self.library.finalizemodel()
        self.library.shutdown()  # Fortran cleanup function.
        # del self.library  # This one doesn't work.
        os.chdir(self.original_dir)

    # Variable Information Functions
    # Note that these call subroutines.
    # In python you expect a function to return something
    # In fortran subroutines can also return something in the input arguments
    # That's why we wrap these manually, we return the input arguments
    def get_var_type (self, name):
        """
        returns type string, compatible with numpy
        """
        name = create_string_buffer(name)
        type_ = create_string_buffer(self.MAXSTRLEN)
        self.library.get_var_type.argtypes = [c_char_p, c_char_p]
        self.library.get_var_type(name, type_)
        return type_.value

    def get_var_rank(self, name):
        """
        returns array rank or 0 for scalar
        """
        name = create_string_buffer(name)
        rank = c_int() # we don't know what size string we get back...
        self.library.get_var_rank.argtypes = [c_char_p, POINTER(c_int)]
        self.library.get_var_rank.restype = None
        self.library.get_var_rank(name, byref(rank))
        return rank.value

    def get_var_shape(self, name):
        """
        returns shape of the array
        """
        rank = self.get_var_rank(name)
        name = create_string_buffer(name)
        arraytype = ndpointer(dtype='int32',
                              ndim=1,
                              shape=(self.MAXDIMS,),
                              flags='F')
        shape = np.empty((self.MAXDIMS,) ,dtype='int32', order='fortran')
        self.library.get_var_shape.argtypes = [c_char_p, arraytype]
        self.library.get_var_shape(name, shape)
        return tuple(shape[:rank])

    def get_nd(self, name):
        """Get an nd array from subgrid library"""

        # How many dimensiosn
        rank = self.get_var_rank(name)
        # The shape array is fixed size
        shape = np.empty((MAXDIMS, ), dtype='int32', order='fortran')
        shape = self.get_var_shape(name)
        # there should be nothing here...
        assert sum(shape[rank:]) == 0
        # variable type name
        type_ = self.get_var_type(name)


        # Store the data in this type
        arraytype = ndpointer(dtype=TYPEMAP[type_],
                              ndim=rank,
                              shape=shape[::-1],
                              flags='F')
        # Create a pointer to the array type
        data = arraytype()
        # The functions get_var_type/_shape/_rank are already wrapped with python function converter
        # get_var isn't
        c_name = create_string_buffer(name)
        get_var = self.library.get_var
        get_var.argtypes = [c_char_p, POINTER(arraytype)]
        get_var.restype = None
        # Get the array
        get_var(c_name, byref(data))
        array = np.asarray(data)
        # Not sure why we need this....
        array = np.reshape(array.ravel(), shape, order='F')
        return array
    def __enter__(self):
        """Return the decorated instance upon entering the ``with`` block.

        We call the :meth:`start` method which starts everything up. Our
        return value is the Fortran library. This is what you get back from
        ``with ... as ...`` so that you can call Fortran functions on it.

        """
        self.start()
        return self

    def __exit__(self, type, value, tb):
        """Clean up what can be cleaned upon exiting the ``with`` block.

        We call the :meth:`stop` method that does the actual work.

        """
        self.stop()
