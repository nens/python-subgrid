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


# TODO replace by numpy.testing assert almost equal
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
class LibSubgridStructuresTest(unittest.TestCase):

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
    def test_compound_rank(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            rank = subgrid.get_var_rank('pumps')
            self.assertEqual(rank, 1)
    @printname
    def test_compound_rank_2donly(self):
        """test compound rank for a model with only 2d"""
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            subgrid.initmodel()
            rank = subgrid.get_var_rank('pumps')
            self.assertEqual(rank, 1)

    @printname
    def test_compound_type(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            type_ = subgrid.get_var_type('pumps')
            self.assertEqual(type_, 'pump')

    @printname
    def test_make_compound(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            valtype = subgrid.make_compound_ctype("pumps")
            # check if the type is a pointer to the compound array type
            # types pointer->array->pumps->id
            self.assertTrue(valtype._type_.__name__.startswith(
                'COMPOUND_Array'))
            self.assertEqual(valtype._type_._type_.__name__, 'COMPOUND')

    @printname
    def test_compound_getnd(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('pumps')
            self.assertEqual(len(df), 1)
            logger.info(df.to_string())

    @printname
    def test_remove_pump(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('pumps')
            self.assertEqual(len(df), 1)
            id = df['id'].irow(0)
            logger.info(id)
            # This deletes a structure, a pump is a structure
            subgrid.discard_structure(id)
            # Now if we get the pumps again it should be empty
            df = subgrid.get_nd('pumps')
            self.assertEqual(len(df), 0)

    @printname
    def test_pump_it_up(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('pumps')
            self.assertEqual(len(df), 1)
            # Increase capacity of all pumps by a factor 10
            df['capacity'] = df['capacity'] * 10
            s1before = subgrid.get_nd('s1').copy()
            subgrid.update(-1)
            s1after = subgrid.get_nd('s1').copy()
            # There should be water movement now, check S1
            self.assertGreater(np.abs(s1after - s1before).sum(), 0)

    @printname
    def test_pump_it_up2(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('pumps')
            self.assertEqual(len(df), 1)
            # Increase capacity of all pumps by a factor 10
            pumpid = df.id.item(0)
            subgrid.set_structure_field("pumps", pumpid,
                                        "capacity", df['capacity'] * 10)
            for i in range(10):
                subgrid.update(-1)
            s1_increase = subgrid.get_nd('s1').copy()
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            for i in range(10):
                subgrid.update(-1)
            s1_default = subgrid.get_nd('s1').copy()
        self.assertGreater(np.abs(s1_increase - s1_default).sum(), 0)

    @printname
    def test_pump_it_up3(self):
        """Check if finalize also resets pumps"""
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('pumps')
            self.assertEqual(len(df), 1)  # Fails ... we have 2 pumps now!

    @printname
    def test_pump_it_up_manual(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('pumps')
            self.assertEqual(len(df), 1)
            # Get the current capacity
            # Make sure you use item(0), otherwise you get a numpy 0d type
            capacity0 = df.capacity.item(0)
            pumpid = df.id.item(0)
            # Increase capacity of all pump1 by a factor 10
            subgrid.set_structure_field("pumps", pumpid,
                                        "oldcapacity", capacity0)
            subgrid.set_structure_field("pumps", pumpid,
                                        "capacity", capacity0 * 10)
            df = subgrid.get_nd('pumps')
            self.assertEqual(df.id.item(0), pumpid)
            capacity1 = df.capacity.item(0)
            self.assertEqual(capacity1, capacity0 * 10)
            oldcapacity = df.oldcapacity.item(0)
            self.assertEqual(oldcapacity, capacity0)

    @printname
    def test_pump_it_up_1ddemocase(self):

        # run both models for a few minutes
        tstop = 3000
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('pumps')
            # Get the current capacity
            # Make sure you use item(0), otherwise you get a numpy 0d type
            capacity0 = df.capacity.item(0)
            pumpid = df.id.item(0)
            # Increase capacity of pump1 by a factor 10
            subgrid.set_structure_field("pumps", pumpid,
                                        "capacity", capacity0 * 10)
            df = subgrid.get_nd('pumps')
            self.assertEqual(df.id.item(0), pumpid)
            capacity1 = df.capacity.item(0)
            self.assertEqual(capacity1, capacity0 * 10)
            while subgrid.get_nd('t1') < tstop:
                subgrid.update(-1)
            s1pumps = subgrid.get_nd('s1').copy()

        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            while subgrid.get_nd('t1') < tstop:
                subgrid.update(-1)
            s1nopumps = subgrid.get_nd('s1').copy()

        self.assertGreater(np.abs(s1pumps - s1nopumps).sum(), 0)

    @printname
    def test_weir_it_out(self):
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('weirs')
            self.assertGreater(len(df), 0)

    @printname
    def test_weir_it_out_strip(self):
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('weirs')
            # we should have stripped the spaces
            self.assertFalse(df['id'].item(0).endswith(' '))

    @printname
    def test_culvert_verpulverd(self):
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('culverts')
            logger.info('Culverts are NOT being verpulverd')
            self.assertEqual(True, False)

    @printname
    def test_back_orifice(self):
        """can we get orifices back as a dataframe"""
        with SubgridWrapper(mdu=self._mdu_path('brouwersdam')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('orifices')
            self.assertGreater(len(df), 0)

    @printname
    def test_back_orifice_id(self):
        """can we change a crest level"""
        with SubgridWrapper(mdu=self._mdu_path('brouwersdam')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('orifices')
            self.assertEqual(df['id'].item(0), '1')

    @printname
    def test_orifice_write_read(self):
        """Write orifice, then read value"""
        with SubgridWrapper(mdu=self._mdu_path('brouwersdam')) as subgrid:
            subgrid.initmodel()
            orifices = subgrid.get_nd('orifices').copy()
            print("aaaa")
            for orifice_idx in range(len(orifices)):
                orifice = orifices.irow(orifice_idx)
                print(orifice.to_dict())

            subgrid.set_structure_field(
                "orifices", str(4),
                "crest_width", float(26.0))

            subgrid.update(-1)

            print("bbbb")
            orifices = subgrid.get_nd('orifices').copy()
            for orifice_idx in range(len(orifices)):
                orifice = orifices.irow(orifice_idx)
                print(orifice.to_dict())


    @printname
    def test_set_back_orifice(self):
        """can we change a crest level"""
        with SubgridWrapper(mdu=self._mdu_path('brouwersdam')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('orifices')
            # Get the current crest_level
            # Make sure you use item(0), otherwise you get a numpy 0d type
            crest_level = df['crest_level'].item(0)
            orificeid = df['id'].item(0)
            subgrid.set_structure_field("orifices", orificeid,
                                        "crest_level", crest_level + 10)
            df = subgrid.get_nd('orifices')
            self.assertEqual(df['crest_level'].item(0), crest_level + 10)

    @printname
    def test_orifice_table(self):
        with SubgridWrapper(mdu=self._mdu_path('brouwersdam')) as subgrid:
            # get a data frame with all the orrifce information
            orifices = subgrid.get_nd('orifices')
            for var in {"crest_level", "crest_width", "branchid", "link_number", "left_calc_point", "right_calc_point"}:
                self.assertIn(var, orifices.columns)

            for i, orifice in orifices.iterrows():
                # should be labeled with increasing indices
                self.assertEqual(orifice["id"].strip(), str(i + 1))
