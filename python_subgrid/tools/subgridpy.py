#!/usr/bin/env python

"""
Run subgrid as a python script with colored output
"""
import argparse
import logging
import os
import sys

from python_subgrid.tests.utils import colorlogs
from python_subgrid.tools.scenario import apply_events, clean_events
from python_subgrid.tools.scenario import AREA_WIDE_RAIN, RainGridContainer
from python_subgrid.tools.scenario import AreaWideGrid
from python_subgrid.tools.scenario import EventContainer
from python_subgrid.tools.scenario import RadarGrid
from python_subgrid.wrapper import SubgridWrapper


logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse the command line arguments
    """
    argumentparser = argparse.ArgumentParser(
        description='Run subgrid')
    argumentparser.add_argument(
        'mdu', help='mdu files to process')
    argumentparser.add_argument(
        "--tend", help="timestamp of end of simulation", type=int)
    argumentparser.add_argument(
        "--scenariodir", help="scenario directory")
    argumentparser.add_argument(
        "--bui",
        help="ontwerpbui from t=0", type=int)
    argumentparser.add_argument(
        "--radar",
        help="radar rain from t=0, dt in iso8601 (2013-10-13T00:00:00Z)")
    argumentparser.add_argument(
        "--color",
        help="Color logs", default=False, action='store_true')
    argumentparser.add_argument(
        "--verbose",
        # USE WITH CARE: THE LOGGING MIGHT BREAK FORTRAN IN CERTAIN
        # CIRCUMSTANCES
        help="Verbose output (including subgrid output)",
        default=False, action='store_true')
    arguments = argumentparser.parse_args()
    return arguments


def main():
    """main program"""
    arguments = parse_args()

    if arguments.color:
        colorlogs()
        # redirect stdout to /dev/null under osx so we get only 1 output stream
        f = open(os.devnull, 'w')
        sys.stderr = f

    logger.info('Subgridpy')
    logger.setLevel(logging.DEBUG)

    if arguments.scenariodir:
        logger.info('Using scenario dir: %s' % arguments.scenariodir)

    scenario = EventContainer(arguments.scenariodir)
    # scenario events from arguments
    if arguments.bui:
        if str(arguments.bui) in AREA_WIDE_RAIN.keys():
            scenario.add(
                AreaWideGrid, sim_time_start=0, sim_time_end=None,
                rain_definition=str(arguments.bui), type=None)
    if arguments.radar:
        scenario.add(
            RadarGrid, sim_time_start=0, sim_time_end=None,
            radar_dt=arguments.radar, sync=1, multiplier=1, type=None)

    logger.info('---- Scenario summary ----')
    for line in scenario.summary():
        logger.info(line)

    subgrid = SubgridWrapper(mdu=arguments.mdu, set_logger=arguments.verbose)
    subgrid.start()
    subgrid.library.initmodel()

    rain_grid_container = RainGridContainer(subgrid)
    subgrid.subscribe_dataset(rain_grid_container.memcdf_name)

    if arguments.tend:
        t_end = arguments.tend
    else:
        # default
        t_end = subgrid.get_nd('tend')
    logger.info('End time (seconds): %r', t_end)

    t = subgrid.get_nd('t1')  # by reference
    while t < t_end:
        logger.info('Doing time %s', t)
        apply_events(subgrid, scenario, rain_grid_container)
        subgrid.update(-1)
        t = subgrid.get_nd('t1')  # by reference

    clean_events(scenario, rain_grid_container)
