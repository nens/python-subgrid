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
import numpy.testing as npt
import pandas

from python_subgrid.wrapper import SubgridWrapper, logger, progresslogger, NotDocumentedError
from python_subgrid.tests.utils import printinfo, scenarios


#import gc
#gc.disable()

# We don't want to know about ctypes here
# only in the test_wrapper and the wrapper itself.


EPSILON = 0.00000001


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
    def test_compound_rank(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            rank = subgrid.get_var_rank('pumps')
            self.assertEqual(rank, 1)
    @printinfo
    def test_compound_rank_2donly(self):
        """test compound rank for a model with only 2d"""
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            subgrid.initmodel()
            rank = subgrid.get_var_rank('pumps')
            self.assertEqual(rank, 1)

    @printinfo
    def test_compound_type(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            type_ = subgrid.get_var_type('pumps')
            self.assertEqual(type_, 'pump')

    @printinfo
    def test_make_compound(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            valtype = subgrid.make_compound_ctype("pumps")
            # check if the type is a pointer to the compound array type
            # types pointer->array->pumps->id
            self.assertTrue(valtype._type_.__name__.startswith(
                'COMPOUND_Array'))
            self.assertEqual(valtype._type_._type_.__name__, 'COMPOUND')

    @printinfo
    def test_compound_getnd(self):
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('pumps')
            self.assertEqual(len(df), 1)
            logger.info(df.to_string())

    @printinfo
    def test_pump_and_manhole(self):
        with SubgridWrapper(mdu=self._mdu_path('duifpolder')) as subgrid:
            subgrid.initmodel()

            # add manhole with capacity of 50m3/s
            subgrid.discharge(80968.2596081587, 443068.9399839948, "flush", 1, 50)
            # after 10 timesteps, pump should have a discharge of 0.2
            for i in range(22):
                q = subgrid.get_nd('q', sliced=True)
                logger.warn("q: %s", q[22008])

                subgrid.update(-1)

            df = subgrid.get_nd('pumps')
            logger.info("pumps: %s", df)
            pump = df[df['id'] == 'pumpstation-11']
            self.assertEqual(1, len(pump))
            npt.assert_equal(22008, pump.link_number.item()-1)
            npt.assert_almost_equal(0.2, pump.capacity.item())

            q = subgrid.get_nd('q', sliced=True)
            npt.assert_almost_equal(0.2, q[22008])

    @printinfo
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

    @printinfo
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

    @printinfo
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

    @printinfo
    def test_pump_it_up3(self):
        """Check if finalize also resets pumps"""
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
        with SubgridWrapper(mdu=self._mdu_path('1dpumps')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('pumps')
            self.assertEqual(len(df), 1)  # Fails ... we have 2 pumps now!

    @printinfo
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

    @printinfo
    def test_pump_it_up_is_active(self):

        # run both models for a few minutes
        tstop = 3000
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('pumps')
            import ipdb
            ipdb.set_trace()
            self.assertTrue(df['is_active'].all())

    @printinfo
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

    @printinfo
    def test_weir_it_out(self):
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('weirs')
            self.assertGreater(len(df), 0)

    @printinfo
    def test_weir_it_out_strip(self):
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('weirs')
            # we should have stripped the spaces
            self.assertFalse(df['id'].item(0).endswith(' '))

    @printinfo
    def test_culvert_verpulverd(self):
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('culverts')
            logger.info('Culverts are NOT being verpulverd')
            self.assertGreater(len(df), 0)

    @printinfo
    def test_back_orifice(self):
        """can we get orifices back as a dataframe"""
        with SubgridWrapper(mdu=self._mdu_path('brouwersdam')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('orifices')
            self.assertGreater(len(df), 0)

    @printinfo
    def test_back_orifice_id(self):
        """can we change a crest level"""
        with SubgridWrapper(mdu=self._mdu_path('brouwersdam')) as subgrid:
            subgrid.initmodel()
            df = subgrid.get_nd('orifices')
            self.assertEqual(df['id'].item(0), '1')

    @printinfo
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


    @printinfo
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

    @printinfo
    def test_orifice_table(self):
        with SubgridWrapper(mdu=self._mdu_path('brouwersdam')) as subgrid:
            # get a data frame with all the orrifce information
            orifices = subgrid.get_nd('orifices')
            for var in {"crest_level", "crest_width", "branchid", "link_number", "left_calc_point", "right_calc_point"}:
                self.assertIn(var, orifices.columns)

            for i, orifice in orifices.iterrows():
                # should be labeled with increasing indices
                self.assertEqual(orifice["id"].strip(), str(i + 1))
if __name__ == '__main__':
    unittest.main()
