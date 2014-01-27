#test_raingrid

import unittest
import logging
import os
import numpy as np
import datetime

#from python_subgrid.wrapper import SubgridWrapper
import python_subgrid.wrapper

from python_subgrid.raingrid import RainGrid


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

    def tearDown(self):
        pass

    def xtest_smoke(self):
        with SubgridWrapper(mdu=self.mdu) as subgrid:
            print 'test load'
            subgrid.initmodel()
            for i in range(5):
                subgrid.update(-1)        

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
        #asdfa
        subgrid.subscribe_dataset(memcdf_name)
        #rain_grid.fill(1.0)  # HDF error
        #rain_grid.update(dt=datetime.datetime(2013,10,15,0,0), multiplier=1.0)
        print 'test load'
        s0 = subgrid.get_nd('s1').copy()
        for i in range(10):
            subgrid.update(-1)        
        s1 = subgrid.get_nd('s1').copy()

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
        asdf
