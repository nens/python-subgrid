"""Utilities. For the moment documentation-generation related."""

import collections
import ctypes
import logging
import os
import platform
try:
    # py3
    import configparser
except ImportError:
    # py2
    import ConfigParser as configparser
import re

from webob.multidict import MultiDict

SUFFIXES = collections.defaultdict(lambda: '.so')
SUFFIXES['Darwin'] = '.dylib'
SUFFIXES['Windows'] = '.dll'
SUFFIX = SUFFIXES[platform.system()]


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


OPTCRE = re.compile(
    r'(?P<option>[^:=\s][^:=]*)'          # very permissive!
    r'\s*(?P<vi>[:=])\s*'                 # any number of space/tab,
    # followed by separator
    # (either : or =), followed
    # by any # space/tab
    r'(?P<value>.*?)'                      # the value, non greedy
    r'\s*(?P<comment>#.*)?'                   # an optional comment
    r'$'                                   # the end of line
)


class MduParser(configparser.ConfigParser):
    """
    Parse an mdu file, a sort of ini file but with fortran numbers and comments
    """
    OPTCRE = OPTCRE


    def getfloat(self, section, option):
        """return float after fixing fortran specific 1d-1 notation"""
        def fixfloat(x):
            """convert fortran numbers (2D-1) to normal numbers"""
            x = str(x).lower()
            x = x.replace('d', 'e').replace('f', 'e')
            return float(x)
        return self._get(section, fixfloat, option)

class MduParserKeepComments(configparser.ConfigParser):
    """
    parse an mdu file, without splitting comments, without lowercasing
    """

    def optionxform(self, optionstr):
        return str(optionstr)
    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            fp.write("[%s]\n" % configparser.DEFAULTSECT)
            for (key, value) in self._defaults.items():
                fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
            fp.write("\n")

        # compute max length:
        maxkey = 0
        maxval = 0
        for section, options in self._sections.items():
            for key, value in options.items():
                maxkey = max(len(key), maxkey)
                # lookup length before comment
                maxval = max(len(value.split("#", 1)[0]), maxval)
        lineformat = ("{key:%d} = {val}" % (maxkey, ))
        for section, options in self._sections.items():
            fp.write("[%s]\n" % section)
            for (key, value) in options.items():
                if key == "__name__":
                    continue
                if (value is not None) or (self._optcre == self.OPTCRE):
                    val = str(value).replace('\n', '\n\t')
                    split = val.split("#", 1) # split of first comment
                    # we have comments in the value, align....
                    if len(split) > 1:
                        valformat = "{val:%d} # {comment}" % (maxval,)
                        val = valformat.format(val=split[0], comment=split[1].strip())

                line = lineformat.format(key=key, val=val)
                fp.write("%s\n" % (line))
            fp.write("\n")


# TODO: merge with MduParser above to a MultiSection Fortran ini file parser.
# TODO: check with Sander for merge
# The idea seems to be that you subclass, but I want initialisation options

class MultiSectionConfigParser(configparser.ConfigParser):
    """
    Yet another type of ini file in use. This time with non-unique sections.
    """
    def __init__(self, *args, **kwargs):
        # ignore dict_type, always use multidict.
        # old style class
        configparser.ConfigParser.__init__(self,
                                           dict_type=MultiDict,
                                           *args, **kwargs)

    def add_section(self, section):
        """Create a new section in the configuration.

        Multiple sections with the same name can exist
        Raise ValueError if name is DEFAULT or any of it's
        case-insensitive variants.
        """
        if section.lower() == "default":
            raise ValueError('Invalid section name: %s' % section)

        self._sections.add(section, self._dict())

    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            fp.write("[%s]\n" % configparser.DEFAULTSECT)
            for (key, value) in self._defaults.items():
                fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
            fp.write("\n")
        for section, options in self._sections.items():
            fp.write("[%s]\n" % section)
            for (key, value) in options.items():
                if key == "__name__":
                    continue
                if (value is not None) or (self._optcre == self.OPTCRE):
                    key = " = ".join((key, str(value).replace('\n', '\n\t')))
                fp.write("%s\n" % (key))
            fp.write("\n")

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
    # http://msdn.microsoft.com/en-us/library/windows
    # /desktop/ms683152(v=vs.85).aspx
    name = 'libdl' + SUFFIX
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

def generate_tables():
    """generate new tables"""
    import argparse
    # TODO circular dependency, move this (wrapper import utils, utils imports wrapper)
    from . import wrapper
    # Implement command line
    # save grid administration file
    # save table data file
    parser = argparse.ArgumentParser(description='Save grid and table administration.')
    parser.add_argument('mdu', help='mdu files to process')
    parser.add_argument('-t', '--table', dest="table", help='table name to generate', default="newtable.tbl")
    parser.add_argument('-g', '--grid', dest="grid", help='grid name to generate', default="newgrid.grd")
    args = parser.parse_args()
    with wrapper.SubgridWrapper(mdu=args.mdu) as subgrid:
        subgrid.initmodel()
        subgrid.save_grid(args.grid)
        subgrid.save_tables(args.table)


def generate_functions_documentation():
    """Script to generate documentation on the wrapped Fortran functions.

    This function is installed via a setuptools console script entry point as
    a script with the same name.

    """
    # Assumption: we're called from the root of the project.
    target_dir = './doc/source/'
    assert os.path.exists(target_dir), "Target dir {} doesn't exist.".format(
        target_dir)
    # Local import, utils is bound to importered, itself, too.
    out = ''
    out += FILE_HEADER

    # TODO circular dependency
    from python_subgrid.wrapper import FUNCTIONS
    out += FUNCTIONS_HEADER
    for function in FUNCTIONS:
        args = ', '.join([arg.__class__.__name__
                          for arg in function['argtypes']])
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

if __name__ == '__main__':
    generate_tables()
