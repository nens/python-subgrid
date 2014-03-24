#!/usr/bin/env python

"""
Run subgrid as a python script with colored output
"""
import os
import argparse
import sys


from python_subgrid.wrapper import SubgridWrapper, logger, progresslogger, NotDocumentedError
from python_subgrid.tests.utils import colorlogs
colorlogs()

try:
    # redirect stdout to /dev/null under osx so we get only 1 output stream
    f = open(os.devnull, 'w')
    sys.stdout = f
except:
    pass

def parse_args():
    """
    Parse the command line arguments
    """
    argumentparser = argparse.ArgumentParser(
        description='Run subgrid')
    argumentparser.add_argument('mdu', help='mdu files to process')
    arguments = argumentparser.parse_args()
    return arguments

def main():
    """main program"""
    arguments = parse_args()

    # Read mdu file
    with SubgridWrapper(mdu=arguments.mdu) as subgrid:
        t_end = subgrid.get_nd('tend')
        t = subgrid.get_nd('t1')
        while t < t_end:
            subgrid.update(-1)
