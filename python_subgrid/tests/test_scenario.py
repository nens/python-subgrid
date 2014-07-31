"""
Test the library on desired behavior by running it on several models.
"""
import unittest
import logging

from python_subgrid.tests.utils import colorlogs
from python_subgrid.tools.scenario import Scenario
from python_subgrid.tools.scenario import RadarGrids
from python_subgrid.tools.scenario import Event

colorlogs()
# We don't want to know about ctypes here
# only in the test_wrapper and the wrapper itself.

import logging
import os


class TestCase(unittest.TestCase):

    def setUp(self):
        self.scenario_path = 'python_subgrid/tests/scenario'
        self.radar_grid_path = os.path.join(
            self.scenario_path, Scenario.radar_grids_filename)
        self.area_wide_rain_grid_path = os.path.join(
            self.scenario_path, Scenario.area_wide_rain_grids_filename)

    def tearDown(self):
        pass

    def test_smoke(self):
        scenario = Scenario()

    def test_smoke2(self):
        scenario = Scenario(self.scenario_path)

    def test_event(self):
        event = Event()
        event.from_file(self.radar_grid_path)
        self.assertEquals(len(event.events()), 1)

    def test_radar_grid(self):
        radar_grid = RadarGrids()
        radar_grid.from_file(self.radar_grid_path)
        # TODO: some special radar grid action