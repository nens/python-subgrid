"""
Test the library on desired behavior by running it on several models.
"""
import logging
import os
import unittest

import numpy as np
import numpy.testing as npt

from python_subgrid.raingrid import RainGrid
from python_subgrid.tests.utils import printinfo, scenarios, colorlogs
from python_subgrid.wrapper import SubgridWrapper, logger

# We don't want to know about ctypes here

# only in the test_wrapper and the wrapper itself.


# Use DelflandiPad by default for now
DEFAULT_SCENARIO = 'delfland_gebiedsbreed'
scenario = os.environ.get('SCENARIO', DEFAULT_SCENARIO)
# By default, we look for scenario dirs in the current working directory. This
# means you need to create symlinks to them.
# Handiest is to use the ``update_testcases.sh`` script to check out
# everything into the testcases directory. This is supported by default.
# An alternative is to set the
# SCENARIO_BASEDIR environment variable.
if 'SCENARIO_BASEDIR' in os.environ:
    scenario_basedir = os.path.abspath(os.environ['SCENARIO_BASEDIR'])
elif 'testcases' in os.listdir('.'):
    scenario_basedir = os.path.abspath('testcases')
else:
    scenario_basedir = os.path.abspath('.')

default_scenario_path = os.path.join(scenario_basedir,
                                     scenarios[scenario]['path'])
models_available = os.path.exists(default_scenario_path)
msg = "Scenario models not available {}".format(default_scenario_path)


colorlogs()
logging.basicConfig()
# TODO: aargh, this logger re-defines the logger imported above!
# TODO: And: don't do basicConfig for logging so globally!
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)





#TODO: get this to work
#@unittest.skipIf(not models_available, msg)
class TestCase(unittest.TestCase):

    def setUp(self):
        self.default_mdu = self._mdu_path(scenario)
        pass

    def tearDown(self):
        pass

    def _mdu_path(self, scenario):
        abs_path = os.path.join(scenario_basedir,
                                scenarios[scenario]['path'])
        return os.path.join(abs_path, scenarios[scenario]['mdu_filename'])

    @printinfo
    def test_000_load_delfland_then_duifp(self):
        """test load a 1d model twice"""
        with SubgridWrapper(mdu=self._mdu_path('delfland_gebiedsbreed')) as subgrid:
            logger.info("loaded delfland")
            subgrid.update(-1)
        with SubgridWrapper(mdu=self._mdu_path('duifp')) as subgrid:
            logger.info("loaded duifpolder")
            subgrid.update(-1)


    @printinfo
    def test_001_load_duifpolder(self):
        """test load a 1d model twice"""
        with SubgridWrapper(mdu=self._mdu_path('duifpolder_slice')):
            logger.info("loaded duifpolder")

    @printinfo
    def test_001_load_duifpolder_default(self):
        """test load"""
        with SubgridWrapper(mdu=self._mdu_path('duifp')):
            logger.info("loaded duifpolder default")

    @printinfo
    def test_001_run_delfland_default(self):
        """test load & run"""
        with SubgridWrapper(mdu=self._mdu_path('delfland_default')) as subgrid:
            logger.info("loaded delfland default")
            subgrid.update(-1)

    @printinfo
    def test_001_load_duifpolder_default_run(self):
        """test load"""
        with SubgridWrapper(mdu=self._mdu_path('duifp')) as subgrid:
            logger.info("loaded duifpolder default")
            for i in xrange(60):
                subgrid.update(-1)

    @printinfo
    def test_001_load_duifpolder_default_raingrid(self):
        """test load"""
        with SubgridWrapper(mdu=self._mdu_path('duifp')) as subgrid:
            logger.info("loaded duifpolder default")
            rain_grid = RainGrid(subgrid, '', initial_value=0.)
            subgrid.subscribe_dataset(rain_grid.memcdf_name)
            logger.info('apply raingrid')
            subgrid.update(-1)

    @printinfo
    def test_001_load_hhnk(self):
        """test load"""
        with SubgridWrapper(mdu=self._mdu_path('hhnk_gebiedsbreed')):
            logger.info("loaded hhnk gebiedsbreed")

    @printinfo
    def test_001_run_hhnk(self):
        """test load"""
        with SubgridWrapper(mdu=self._mdu_path('hhnk_gebiedsbreed')) as subgrid:
            logger.info("loaded hhnk gebiedsbreed")
            for i in xrange(600):
                subgrid.update(-1)

    @printinfo
    def test_001_run_beemster(self):
        with SubgridWrapper(mdu=self._mdu_path('beemster')) as subgrid:
            logger.info("loaded beemster")
            for i in xrange(20):
                subgrid.update(-1)
            logger.info("vol1 %r" % np.sum(subgrid.get_nd('vol1')))

    @printinfo
    def test_001_load_duifpolder_2d(self):
        """test load a model with groundwater twice"""
        with SubgridWrapper(mdu=self._mdu_path('duifpolder_2d')) as subgrid:
            logger.info("loaded duifpolder 2d: 1 of 2")
            subgrid.initmodel()
            subgrid.update(-1)
            npt.assert_allclose(subgrid.get_nd('sg'), -8)
        with SubgridWrapper(mdu=self._mdu_path('duifpolder_2d')) as subgrid:
            logger.info("loaded duifpolder 2d: 2 of 2")
            subgrid.initmodel()

    @printinfo
    def test_000_testcase_culvert(self):
        """test load and init testmodel with culvert"""
        with SubgridWrapper(mdu=self._mdu_path('testcase')) as subgrid:
            logger.info("loaded testcase")
            subgrid.initmodel()
            subgrid.update(-1)
        with SubgridWrapper(mdu=self._mdu_path('testcase')) as subgrid:
            logger.info("loaded testcase")
            subgrid.initmodel()
            subgrid.update(-1)

    @printinfo
    def test_1ddemo_heerenveen(self):
        """load the heerenveen model after loading a 1d model"""
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)
        with SubgridWrapper(mdu=self._mdu_path('heerenveen')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)

    @printinfo
    def test_heerenveen(self):
        """load the heereveent mode"""
        with SubgridWrapper(mdu=self._mdu_path('heerenveen')) as subgrid:
            subgrid.initmodel()
            for _ in range(10):
                subgrid.update(-1)

    @printinfo
    def test_load_1ddemo_1ddemo(self):
        """load the model twice"""
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)

    @printinfo
    def test_load_1ddemo_wijder(self):
        """load the 1d demo model, then the wijdewormer"""
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)
        with SubgridWrapper(mdu=self._mdu_path('wijdewormer')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)
            pumps = subgrid.get_nd('pumps')  # pandas DataFrame
            pumps.to_dict()
            self.assertEquals(pumps.to_dict()['id'].keys()[0], 0)

    @printinfo
    def test_kaapstad_wkt(self):
        """load kaapstad and extract the well known text"""
        with SubgridWrapper(mdu=self._mdu_path('kaapstad_centrum')) as subgrid:
            subgrid.initmodel()
            wkt = subgrid.get_nd('wkt')
        # we should have some coordinate system
        self.assertTrue("GEOGCS" in wkt)
    #@unittest.skip
    @printinfo
    def test_manhole_mozambique(self):
        """load the mozambique model and add a discharge point"""
        mdu_filename = self._mdu_path('mozambique')
        with SubgridWrapper(mdu=mdu_filename) as subgrid:
            manhole_name = 'test_manhole'
            x = 695570
            y = 7806336
            discharge_value = 5000.0
            itype = 1
            subgrid.discharge(x, y, manhole_name, itype, discharge_value)
            for _ in range(10):
                subgrid.update(-1)

    @printinfo
    def test_hhnk(self):
        """test if we can start 1d democase, followed by hhnk"""
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            for _ in range(10):
                subgrid.update(-1)
        with SubgridWrapper(mdu=self._mdu_path('hhnk')) as subgrid:
            subgrid.initmodel()
            for _ in range(10):
                subgrid.update(-1)

    @printinfo
    def test_changebathy_heerenveen(self):
        with SubgridWrapper(mdu=self._mdu_path('heerenveen')) as subgrid:
            for i in range(5):
                print('doing %d...' % i)
                print subgrid.update(-1)  # -1 = use default model time

            xc = 188733.
            yc = 553957.
            sz = 70
            bval = -0.5
            bmode = 1  # 0 = relative, 1 = absolute

            print('changing bathymetry...')
            subgrid.changebathy(xc, yc, sz, bval, bmode)

            print('continue simulation...')
            for i in range(5):
                print('doing %d...' % i)
                print subgrid.update(-1)  # -1 = use default model time

    @printinfo
    def test_manhole_hhnk(self):
        """add a manhole to hhnk model"""
        with SubgridWrapper(mdu=self._mdu_path('hhnk')) as subgrid:
            subgrid.initmodel()
            manhole_name = 'test_manhole'
            x = 115741
            y = 517257
            discharge_value = 250.0
            itype = 1
            subgrid.discharge(x, y, manhole_name, itype, discharge_value)
            for _ in range(100):
                subgrid.update(-1)

    @printinfo
    def test_grid_hhnk(self):
        """generate grid in hhnk -> fails if old version grid file already exists"""
        with SubgridWrapper(mdu=self._mdu_path('hhnk_gebiedsbreed')) as subgrid:
            subgrid.save_grid(os.path.join('admin', 'gridhhnk_hhnk.grd'))

    @printinfo
    def test_grid_delfland(self):
        """generate grid in delfland"""
        with SubgridWrapper(mdu=self._mdu_path('delfland_gebiedsbreed')) as subgrid:
            subgrid.save_grid(os.path.join('admin', 'griddelfland_gebiedsbreed.grd'))
    @printinfo
    def test_delfland_before_duip(self):
        """generate grid in delfland"""
        with SubgridWrapper(mdu=self._mdu_path('delfland_gebiedsbreed')) as subgrid:
            subgrid.update(-1)
        with SubgridWrapper(mdu=self._mdu_path('duifp')) as subgrid:
            subgrid.update(-1)

    @printinfo
    def test_duifpolder_slice(self):
        """generate grid in duifpolder slice"""
        with SubgridWrapper(mdu=self._mdu_path('duifpolder_slice')) as subgrid:
            subgrid.update(-1)

    @printinfo
    def test_back_orifice_rain(self):
        """Orifice with rain"""
        with SubgridWrapper(mdu=self._mdu('brouwersdam')) as subgrid:
            rain_grid = RainGrid(
                subgrid,
                initial_value=9.)
            subgrid.subscribe_dataset(rain_grid.memcdf_name)
            for _ in range(5):
                subgrid.update(-1)

    @printinfo
    @unittest.skip("https://issuetracker.deltares.nl/browse/THREEDI-169")
    def test_manhole_workflow(self):
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            manhole_name = 'test_manhole'
            x = 85830.97071920538
            y = 448605.8983910042
            discharge_value = 100.0
            itype = 1
            # add it
            for _ in range(5):
                deltas = np.linspace(0, 100000, num=5)
                for i, delta in enumerate(deltas):
                    subgrid.discharge(x + delta, y + delta,
                                      "%s_%s" % (manhole_name, i),
                                      itype, discharge_value)
                subgrid.update(-1)
                # reinitialize
                subgrid.initmodel()
                subgrid.update(-1)
                # remove it
                for delta in deltas:
                    subgrid.discard_manhole(x + delta, y + delta)
                # add it again
                subgrid.update(-1)
    @printinfo
    def test_testcase(self):
        with SubgridWrapper(mdu=self._mdu_path('testcase')) as subgrid:
            subgrid  # pyflakes
        with SubgridWrapper(mdu=self._mdu_path('testcase')) as subgrid:
            subgrid  # pyflakes


if __name__ == '__main__':
    unittest.main()
