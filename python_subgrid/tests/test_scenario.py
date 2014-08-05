"""
Test the library on desired behavior by running it on several models.
"""
import unittest
import logging

from python_subgrid.tests.utils import colorlogs
from python_subgrid.tools.scenario import RadarGrid
from python_subgrid.tools.scenario import Event
from python_subgrid.tools.scenario import EventContainer

colorlogs()
# We don't want to know about ctypes here
# only in the test_wrapper and the wrapper itself.

import logging
import os


class TestCase(unittest.TestCase):

    def setUp(self):
        self.scenario_path = 'python_subgrid/tests/scenario'
        self.radar_grid_path = os.path.join(
            self.scenario_path, EventContainer.radar_grids_filename)
        self.area_wide_rain_grid_path = os.path.join(
            self.scenario_path, EventContainer.area_wide_rain_grids_filename)

    def tearDown(self):
        pass

    def test_smoke(self):
        event_container = EventContainer()

    def test_events(self):
        event_container = EventContainer(self.scenario_path)
        self.assertEquals(len(
            event_container.events(event_object=RadarGrid)), 1)

    def test_radar_grid_time(self):
        event_container = EventContainer(self.scenario_path)
        self.assertEquals(
            len(event_container.events(
                event_object=RadarGrid, sim_time=120.)), 1)

    def test_radar_grid_start_within(self):
        event_container = EventContainer(self.scenario_path)
        self.assertEquals(len(event_container.events(
            event_object=RadarGrid, sim_time=130, start_within=30)), 1)
        self.assertEquals(len(event_container.events(
            event_object=RadarGrid, sim_time=150, start_within=20)), 0)
        # TODO: some special radar grid action

        # # From player.py
        # logger.info('Preparing radar rain grid...')
        # size_x, size_y = 500, 500
        # self.rain_grid = RainGrid(
        #     self, self.radar_url_template,
        #     initial_value=0.,
        #     size_x=size_x, size_y=size_y)

        # self.subscribe_dataset(self.container_rain_grid.memcdf_name)
