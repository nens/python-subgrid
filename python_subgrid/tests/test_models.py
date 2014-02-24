"""
Test the library on desired behavior by running it on several models.
"""
import unittest
import os
import logging
import io
from functools import wraps

from nose.plugins.attrib import attr
import numpy as np
import pandas

from python_subgrid.wrapper import SubgridWrapper, logger, progresslogger
from python_subgrid.utils import NotDocumentedError

#import gc
#gc.disable()

# We don't want to know about ctypes here
# only in the test_wrapper and the wrapper itself.


EPSILON = 0.00000001

scenarios = {
    '1dpumps': {
        'path': '1dpumptest',
        'mdu_filename': "1d2d_kunstw.mdu",
    },
    '1d-democase': {
        'path': '1d-democase',
        'mdu_filename': "1D-democase.mdu",
    },
    'wijdewormer': {
        'path': 'wijdewormer_spatiallite',
        'mdu_filename': "wijdewormer_spatiallite.mdu",
    },
    'DelflandiPad': {
        'path': 'delfland-model-voor-3di',
        'mdu_filename': "hhdlipad.mdu",
    },
    'hhnk': {
        'path': 'hhnkipad',
        'mdu_filename': "HHNKiPad.mdu",
    },
    'heerenveen': {
        'path': 'heerenveen',
        'mdu_filename': "heerenveen.mdu",
    },
    'betondorp': {
        'path': 'betondorp',
        'mdu_filename': "betondorp_waternet.mdu",
    },
    'Kaapstad': {
        'path': 'Kaapstad',
        'mdu_filename': "Kaapstad.mdu",
    },
    'kaapstad_centrum': {
        'path': 'kaapstad_centrum',
        'mdu_filename': "kaapstad_centrum.mdu",
    },
    'mozambique': {
        'path': 'mozambique',
        'mdu_filename': "mozambique.mdu",
    },
    'boezemstelsel-delfland': {
        'path': 'boezemstelsel-delfland',
        'mdu_filename': "Boezem_HHD.mdu",
    },
    'heerenveen': {
        'path': 'heerenveen',
        'mdu_filename': "heerenveen.mdu",
    },
    'brouwersdam': {
        'path': 'brouwersdam',
        'mdu_filename': "brouwersdam.mdu",
    },
}

# Use DelflandiPad by default for now
DEFAULT_SCENARIO = 'DelflandiPad'
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


def float_equals(a, b):
    return abs(a-b) < EPSILON



def printname(f):
    """print the name of the test being called"""
    # needed because it does not show up if the test segfaults
    # this can probably be done easier
    @wraps(f)
    def wrapper(*args, **kwds):
        print("### running test {f}".format(f=f))
        return f(*args, **kwds)
    return wrapper

#TODO: get this to work
#@unittest.skipIf(not models_available, msg)
class LibSubgridModelsTest(unittest.TestCase):

    def setUp(self):
        self.default_mdu = self._mdu_path(scenario)
        pass

    def tearDown(self):
        pass

    def _mdu_path(self, scenario):
        abs_path = os.path.join(scenario_basedir,
                                scenarios[scenario]['path'])
        return os.path.join(abs_path, scenarios[scenario]['mdu_filename'])

    @printname
    def test_load_1d(self):
        """test load a 1d model twice"""
        for i in range(2):
            with SubgridWrapper(mdu=self._mdu_path('boezemstelsel-delfland')):
                print('test load #%r' % i)

    @printname
    def test_1ddemo_heerenveen(self):
        """load the heerenveen model after loading a 1d model"""
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)
        with SubgridWrapper(mdu=self._mdu_path('heerenveen')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)

    @printname
    def test_heerenveen(self):
        """load the heereveent mode"""
        with SubgridWrapper(mdu=self._mdu_path('heerenveen')) as subgrid:
            subgrid.initmodel()
            for _ in range(10):
                subgrid.update(-1)

    @printname
    def test_load_1ddemo_1ddemo(self):
        """load the model twice"""
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)

    @printname
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

    @printname
    def test_kaapstad_wkt(self):
        """load kaapstad and extract the well known text"""
        with SubgridWrapper(mdu=self._mdu_path('kaapstad_centrum')) as subgrid:
            subgrid.initmodel()
            wkt = subgrid.get_nd('wkt')
        # we should have some coordinate system
        self.assertTrue("GEOGCS" in wkt)
    #@unittest.skip
    @printname
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

    @printname
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

    @printname
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

    @printname
    def test_testcase(self):
        with SubgridWrapper(mdu=self._mdu_path('testcase')) as subgrid:
            pass
        with SubgridWrapper(mdu=self._mdu_path('testcase')) as subgrid:
            pass
