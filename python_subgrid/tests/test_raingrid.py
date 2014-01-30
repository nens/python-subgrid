#test_raingrid

import unittest
import logging
import os
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


class RainGridTest(unittest.TestCase):

    def setUp(self):
        self.mdu = os.path.join(scenario_basedir,
                                'hhnkipad', 'HHNKiPad.mdu')

    def _mdu(self, model_slug):
        return os.path.join(scenario_basedir,
                            scenarios[model_slug]['path'], 
                            scenarios[model_slug]['mdu_filename'])


    def tearDown(self):
        pass

    def xtest_smoke(self):
        with SubgridWrapper(mdu=self.mdu) as subgrid:
            print 'test load'
            subgrid.initmodel()
            for i in range(5):
                subgrid.update(-1)        

    def test_smoke2(self):
        mdu1 = self._mdu('hhnk')
        mdu2 = self._mdu('1d-democase')
        with SubgridWrapper(mdu=mdu1) as subgrid:
            subgrid.initmodel()
            for i in range(2):
                subgrid.update(-1)        
        with SubgridWrapper(mdu=mdu2) as subgrid:
            subgrid.initmodel()
            for i in range(2):
                subgrid.update(-1)        
        with SubgridWrapper(mdu=mdu1) as subgrid:
            subgrid.initmodel()
            for i in range(2):
                subgrid.update(-1)        

    def test_smoke3(self):
        """RuntimeError: Can't add HDF5 file metadata"""
        with SubgridWrapper(mdu=self.mdu) as subgrid:
            rain_grid = RainGrid(
                subgrid, 
                initial_value=9.)
            subgrid.subscribe_dataset(rain_grid.memcdf_name)
        with SubgridWrapper(mdu=self.mdu) as subgrid:
            rain_grid2 = RainGrid(
                subgrid,
                initial_value=1.)
            subgrid.subscribe_dataset(rain_grid2.memcdf_name)

    def test_basic(self):
        url_template = 'http://opendap.nationaleregenradar.nl/thredds/dodsC/radar/TF0005_A/{year}/{month}/01/RAD_TF0005_A_{year}{month}01000000.h5'
        memcdf_name = 'precipitation.nc'

        subgrid = python_subgrid.wrapper.SubgridWrapper(mdu=self.mdu)
        python_subgrid.wrapper.logger.setLevel(logging.DEBUG)
        subgrid.start()

        #subgrid.initmodel()

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

        #print(s1-s0)
        #print('rainfall sum')
        #print(np.sum(rain_grid.rainfall_var))
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

    def test_opendap(self):
        print('opendap test')
        url_template = 'http://opendap.nationaleregenradar.nl/thredds/dodsC/radar/TF0005_A/{year}/{month}/01/RAD_TF0005_A_{year}{month}01000000.h5'
        memcdf_name = 'precipitation.nc'

        subgrid = python_subgrid.wrapper.SubgridWrapper(mdu=self.mdu)
        python_subgrid.wrapper.logger.setLevel(logging.DEBUG)
        subgrid.start()

        #subgrid.initmodel()

        rain_grid = RainGrid(
            subgrid, url_template, 
            memcdf_name=memcdf_name, initial_value=0.)
        #asdfa
        #rain_grid.fill(1.0)
        subgrid.subscribe_dataset(memcdf_name)
        rain_grid.update(dt=datetime.datetime(2013,10,15,0,0), multiplier=1000.0)
        s0 = subgrid.get_nd('s1').copy()
        v0 = subgrid.get_nd('vol1').copy()
        for i in range(12):
            subgrid.update(-1)        
        s1 = subgrid.get_nd('s1').copy()
        v1 = subgrid.get_nd('vol1').copy()

        for i in range(12):
            subgrid.update(-1)        
        v2 = subgrid.get_nd('vol1').copy()

        #print(s1-s0)
        #print('rainfall sum')
        #print(np.sum(rain_grid.rainfall_var))
        print('shape of dps')
        print(subgrid.get_nd('dps').shape)
        print('s0 sum')
        print(np.sum(s0))
        print('s1 sum')
        print(np.sum(s1))
        print('s1-s0 sum')
        print(np.sum(s1-s0))
        print('v0, v1, v1-v0, v2-v1 sum')
        print(np.sum(v0))
        print(np.sum(v1))
        print(np.sum(v1-v0))
        print(np.sum(v2-v1))
        asdf

if __name__ == '__main__':
    unittest.main()
