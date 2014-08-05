#!/usr/bin/env python

"""
Run subgrid as a python script with colored output
"""
import os
import argparse
import sys
import logging
import numpy as np

from python_subgrid.wrapper import SubgridWrapper, logger, progresslogger, NotDocumentedError
from python_subgrid.tests.utils import colorlogs
from python_subgrid.tools.scenario import EventContainer
from python_subgrid.tools.scenario import RadarGrid
from python_subgrid.tools.scenario import AreaWideGrid
from python_subgrid.raingrid import RainGridContainer
from python_subgrid.raingrid import AREA_WIDE_RAIN
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
    argumentparser.add_argument("--bui", help="scenario directory", type=int)
    arguments = argumentparser.parse_args()
    return arguments


def main():
    """main program"""
    logger.setLevel(logging.DEBUG)
    logger.info('Subgridpy')
    arguments = parse_args()

    if arguments.scenariodir:
        logger.info('Using scenario dir: %s' % arguments.scenariodir)
    scenario = EventContainer(arguments.scenariodir)

    # scenario events from arguments
    if arguments.bui:
        if str(arguments.bui) in AREA_WIDE_RAIN.keys():
            scenario.add(
                AreaWideGrid, sim_time_start=0, sim_time_end=None, 
                rain_definition=str(arguments.bui), type=None)

    logger.info('---- Scenario summary ----')
    for line in scenario.summary():
        logger.info(line)

    radar_url_template = 'http://opendap.nationaleregenradar.nl/thredds/dodsC/radar/TF0005_A/{year}/{month}/01/RAD_TF0005_A_{year}{month}01000000.h5'

    subgrid = SubgridWrapper(mdu=arguments.mdu, set_logger=False)
    subgrid.start()
    if 1:  # if you wanna see python errors...

    #with SubgridWrapper(mdu=arguments.mdu, set_logger=False) as subgrid:
        subgrid.library.initmodel()
        rain_grid_container = RainGridContainer(subgrid)
        subgrid.subscribe_dataset(rain_grid_container.memcdf_name)

        dt = subgrid.get_nd('dt')
        logger.info('Step size dt (seconds): %r' % dt)
        if arguments.tend:
            t_end = arguments.tend
        else:
            # default
            t_end = subgrid.get_nd('tend')

        t = subgrid.get_nd('t1')  # by reference
        previous_t = -1  # t1 starts at 0

        # statistics
        stats = {}
        first_timestep = True

        logger.info('---- starting ----')

        while t < t_end:
            sim_time = float(t)
            radar_grid_changed = False
            logger.info('Doing time %f' % sim_time)
            # starting scenario events
            events_init = scenario.events(
                sim_time=sim_time, start_within=sim_time-previous_t)
            for event in events_init:
                logger.info('Init event: %s' % str(event))
                if isinstance(event, RadarGrid):
                    event.init(subgrid, radar_url_template)
                    rain_grid_container.register(event.memcdf_name)
                elif isinstance(event, AreaWideGrid):
                    event.init(subgrid)
                    rain_grid_container.register(event.memcdf_name)

            # finished scenario events
            events_finish = scenario.events(
                sim_time=sim_time, ends_within=dt)
            for event in events_finish:
                logger.info('Finish event: %s' % str(event))
                if isinstance(event, RadarGrid):
                    rain_grid_container.unregister(event.memcdf_name)
                    radar_grid_changed = True
                elif isinstance(event, AreaWideGrid):
                    rain_grid_container.unregister(event.memcdf_name)
                    radar_grid_changed = True

            # active scenario events
            events = scenario.events(sim_time=sim_time)
            for event in events:
                # logger.info('Update event: %s' % str(event))
                if isinstance(event, RadarGrid):
                    changed = event.update(sim_time)
                    if changed:
                        radar_grid_changed = True
                if isinstance(event, AreaWideGrid):
                    changed = event.update(sim_time)
                    if changed:
                        radar_grid_changed = True
            if radar_grid_changed:
                # update container
                rain_grid_container.update()

            previous_t = float(t)
            subgrid.update(-1)

            if first_timestep:
                stats['v0'] = subgrid.get_nd('vol1').copy()
                first_timestep = False

        logger.info('Cleaning up...')
        for event in scenario.events():
            if isinstance(event, RadarGrid):
                logger.info('deleting temp file %s...' % event.memcdf_name)
                event.delete_memcdf()
            elif isinstance(event, AreaWideGrid):
                logger.info('deleting temp file %s...' % event.memcdf_name)
                event.delete_memcdf()
        logger.info('deleting temp file %s...' % rain_grid_container.memcdf_name)
        rain_grid_container.delete_memcdf()

        # testing / stats
        logger.info('Statistics')
        stats['v1'] = subgrid.get_nd('vol1').copy()
        stats['v0_sum'] = np.sum(stats['v0'])
        stats['v1_sum'] = np.sum(stats['v1'])

        logger.info('v0: %0.1f' % stats['v0_sum'])
        logger.info('v1: %0.1f' % stats['v1_sum'])
        logger.info('v1-v0: %0.1f' % (stats['v1_sum'] - stats['v0_sum']))

