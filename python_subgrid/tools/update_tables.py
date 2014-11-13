#!/usr/bin/env python

"""
Generate tables for all subdirectories that have an mdu file in it
"""
import os
import re
import subprocess
import ConfigParser
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# extended with comments
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

# Ignore comments, don't bother to subclass
ConfigParser.ConfigParser.OPTCRE = OPTCRE


def files():
    """find all the mdu files"""
    prunes = {".hglf", ".hg", ".git", ".svn", ".ipynb_checkpoints"}
    for curdir, dirs, files in os.walk("."):
        for prune in prunes:
            if prune in dirs:
                dirs.remove(prune)
        for filename in files:
            _, ext = os.path.splitext(filename)
            if ext.lower() == ".mdu":
                fullpath = os.path.join(curdir, filename)
                yield fullpath


def main():
    """loop over all directories, lookup the mdu file, if it is found update the
    tables

    """
    for fullpath in files():
        dirname, filename = os.path.split(fullpath)

        parser = ConfigParser.ConfigParser()
        parser.read(fullpath)
        try:
            # Find the grid , if it's empty use grid.grd
            gridfile = parser.get("grid", "gridadminfile") or "grid.grd"
        except ConfigParser.NoSectionError:
            # no grid section
            logger.warn("could not find grid section in {}".format(fullpath))
            gridfile = "grid.grd"
        except ConfigParser.NoOptionError:
            logger.warn("could not find gridadminfile in {}".format(fullpath))
            gridfile = "grid.grd"

        try:
            # Find the table, if it's empty use table.tbl
            tablefile = parser.get("grid", "tabledatafile") or "table.tbl"
        except ConfigParser.NoSectionError:
            # no grid section
            logger.warn("could not find grid section in {}".format(fullpath))
            tablefile = "table.tbl"
        except ConfigParser.NoOptionError:
            logger.exception("could not find grid->tabledatafile in %s",
                             fullpath)
            tablefile = "table.tbl"

        logger.info(
            "Writing grids for %s to %s and tables to %s in directory %s",
            filename, gridfile, tablefile, dirname)
        # start the model in a subprocess
        process = subprocess.Popen(
            ["python",
             "-m", "python_subgrid.utils",
             "-g", gridfile,
             "-t", tablefile,
             filename],
            cwd=dirname,  # run in the model directory
            stdout=subprocess.PIPE,  # redirect output to the pipe
            stderr=subprocess.STDOUT  # 2>&1
        )
        returncode = process.wait()
        if returncode:
            logger.info("process failed")
            # show the output
            print(process.stdout.read())


if __name__ == '__main__':
    main()
