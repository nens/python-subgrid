#!/usr/bin/env python

"""
Run subgrid as a python script with colored output
"""
import os
import argparse
import sys
import logging

from python_subgrid.wrapper import SubgridWrapper, logger, progresslogger, NotDocumentedError
from python_subgrid.tests.utils import colorlogs
from python_subgrid.tools.scenario import Scenario
colorlogs()

logger = logging.getLogger(__name__)


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
    argumentparser.add_argument("--tend", help="timestamp of end of simulation", type=int)
    argumentparser.add_argument("--scenariodir", help="scenario directory")
    arguments = argumentparser.parse_args()
    return arguments


def main():
    """main program"""
    arguments = parse_args()

    if arguments.scenariodir:
        logger.info(arguments.scenariodir)
    scenario = Scenario(arguments.scenariodir)

    # Read mdu file
    with SubgridWrapper(mdu=arguments.mdu, set_logger=False) as subgrid:
        if arguments.tend:
            t_end = arguments.tend
        else:
            # default
            t_end = subgrid.get_nd('tend')
        t = subgrid.get_nd('t1')
        while t < t_end:
            subgrid.update(-1)
