"""
Test the library on desired behavior by running it on several models.
"""
import unittest
import logging

from python_subgrid.tests.utils import printinfo, colorlogs
from python_subgrid.tools.scenario import Scenario
from python_subgrid.tools.scenario import RadarGrids

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

    @printinfo
    def test_smoke(self):
        scenario = Scenario()

    @printinfo
    def test_smoke2(self):
        scenario = Scenario(self.scenario_path)


    @printinfo
    def test_radar_grid(self):
        radar_grid = RadarGrids()
        radar_grid.from_file(self.radar_grid_path)
        asdf