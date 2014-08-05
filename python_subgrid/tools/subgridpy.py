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
#colorlogs()

logger = logging.getLogger(__name__)


try:
    # redirect stdout to /dev/null under osx so we get only 1 output stream
    #f = open(os.devnull, 'w')
    #sys.stdout = f
    pass
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
    logger.setLevel(logging.DEBUG)
    logger.info('Subgridpy')
    arguments = parse_args()

    if arguments.scenariodir:
        logger.info('Using scenario dir: %s' % arguments.scenariodir)
    scenario = Scenario(arguments.scenariodir)

    # Read mdu file
    with SubgridWrapper(mdu=arguments.mdu, set_logger=False) as subgrid:
        dt = subgrid.get_nd('dt')
        logger.info('Step size dt (seconds): %r' % dt)
        if arguments.tend:
            t_end = arguments.tend
        else:
            # default
            t_end = subgrid.get_nd('tend')

        t = subgrid.get_nd('t1')  # by reference
        while t < t_end:
            logger.info('Doing time %f' % t)
            subgrid.update(-1)
            # see if there are scenario items
            radar_grid_events = scenario.radar_grids.events(float(t))
            if radar_grid_events:
                logger.info('Radar grid event: %r' % radar_grid_events)
