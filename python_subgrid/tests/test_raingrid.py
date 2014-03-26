#test_raingrid

import unittest
import logging
import os
import sys
import numpy as np
import datetime


#from python_subgrid.wrapper import SubgridWrapper
import python_subgrid.wrapper

from python_subgrid.wrapper import SubgridWrapper

from python_subgrid.raingrid import RainGrid
from python_subgrid.tests.test_functional import scenarios


if 'SCENARIO_BASEDIR' in os.environ:
    scenario_basedir = os.path.abspath(os.environ['SCENARIO_BASEDIR'])
elif 'testcases' in os.listdir('.'):
    scenario_basedir = os.path.abspath('testcases')
else:
    scenario_basedir = os.path.abspath('.')


class TestCase(unittest.TestCase):

    def setUp(self):
        self.mdu = self._mdu('delfland_gebiedsbreed')

    def _mdu(self, model_slug):
        return os.path.join(scenario_basedir,
                            scenarios[model_slug]['path'],
                            scenarios[model_slug]['mdu_filename'])


    def tearDown(self):
        pass

    def test_constant_grid(self):
        """Add grid to 1 model and then to another one"""
        with SubgridWrapper(mdu=self.mdu) as subgrid:
            rain_grid = RainGrid(
                subgrid,
                initial_value=9.)
            subgrid.subscribe_dataset(rain_grid.memcdf_name)
        with SubgridWrapper(mdu=self._mdu('duifp')) as subgrid:
            rain_grid2 = RainGrid(
                subgrid,
                initial_value=1.)
            subgrid.subscribe_dataset(rain_grid2.memcdf_name)
            subgrid.update(-1)

    def test_opendap_grid(self):
        url_template = 'http://opendap.nationaleregenradar.nl/thredds/dodsC/radar/TF0005_A/{year}/{month}/01/RAD_TF0005_A_{year}{month}01000000.h5'
        memcdf_name = 'precipitation.nc'

        subgrid = python_subgrid.wrapper.SubgridWrapper(mdu=self.mdu)
        python_subgrid.wrapper.logger.setLevel(logging.DEBUG)
        subgrid.start()

        rain_grid = RainGrid(
            subgrid, url_template,
            memcdf_name=memcdf_name, initial_value=9.)
        subgrid.subscribe_dataset(memcdf_name)
        rain_grid.fill(1.0)
        s0 = subgrid.get_nd('s1').copy()
        v0 = subgrid.get_nd('vol1').copy()
        for i in range(12):
            subgrid.update(-1)
        s1 = subgrid.get_nd('s1').copy()
        v1 = subgrid.get_nd('vol1').copy()

        print('shape of dps')
        print(subgrid.get_nd('dps').shape)
        print('s0 sum')
        print(np.sum(s0))
        print('s1 sum')
        print(np.sum(s1))
        print('s1-s0 sum')
        print(np.sum(s1-s0))
        print('v0, v1, v1-v0 sum')
        print(np.sum(v0))
        print(np.sum(v1))
        print(np.sum(v1-v0))




if __name__ == '__main__':
    unittest.main()
