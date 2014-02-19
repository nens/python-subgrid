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
class LibSubgridTest(unittest.TestCase):

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
    def test_logging(self):
        subgrid = SubgridWrapper()
        foundmessage = False

        # Create a new handler
        stream = io.BytesIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)

        # if the model logs it is stored in the handler
        subgrid.start()

        # flush
        handler.flush()
        foundmessage = stream.getvalue()

        # cleanup
        logger.removeHandler(handler)

        # we should have some messages
        self.assertTrue(foundmessage)

    @printname
    def test_progress(self):
        """test progress handler"""
        subgrid = SubgridWrapper(mdu=self.default_mdu)
        foundmessage = False

        # Create a new handler
        stream = io.BytesIO()
        handler = logging.StreamHandler(stream)
        progresslogger.addHandler(handler)

        # if the model logs it is stored in the handler
        subgrid.start()

        # flush
        handler.flush()
        foundmessage = stream.getvalue()

        # cleanup
        progresslogger.removeHandler(handler)

        # we should have some messages
        self.assertTrue(foundmessage)

    @printname
    def test_info(self):
        """test if we can print info"""
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            subgrid.subgrid_info()

    @attr('debug')
    @printname
    def test_load(self):
        """test load model twice"""
        for i in range(2):
            with SubgridWrapper(mdu=self.default_mdu):
                print('test load #%r' % i)


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

    @printname
    def test_timesteps(self):
        """test the model for 10 timesteps"""
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            for _ in range(10):
                # -1 = use default model timestep.
                subgrid.update(-1)

    @printname
    def test_dropinstantrain(self):
        """test if we can call dropinstantrain a few times"""
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            subgrid.initmodel()
            x = 85830.97071920538
            y = 448605.8983910042
            clouddiam = 100.0
            rainfall = 100.0
            # do ome timesteps
            for _ in range(10):
                # rain
                subgrid.dropinstantrain(x, y, clouddiam, rainfall)
                # compute
                subgrid.update(-1)

    @printname
    def test_manhole(self):
        """use discharge points to simulate manholes"""
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            manhole_name = 'test_manhole'
            x = 85830.97071920538
            y = 448605.8983910042
            discharge_value = 100.0
            itype = 1
            subgrid.discharge(x, y, manhole_name, itype, discharge_value)
            for _ in range(10):
                subgrid.update(-1)
                subgrid.discharge(
                    x, y,
                    manhole_name, 1, discharge_value)

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
    def test_discard_manhole(self):
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            manhole_name = 'test_manhole'
            x = 85830.97071920538
            y = 448605.8983910042
            discharge_value = 100.0
            itype = 1
            subgrid.discharge(x, y, manhole_name, itype, discharge_value)
            subgrid.discard_manhole(x, y)

    @printname
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

    @printname
    def test_get_var_rank(self):
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            subgrid.initmodel()
            rank = subgrid.get_var_rank('s1')
            self.assertEqual(1, rank)

    @printname
    def test_get_var_type(self):
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            subgrid.initmodel()
            typename = subgrid.get_var_type('s1')
            self.assertEqual(typename, 'double')

    @printname
    def test_get_var_shape(self):
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            subgrid.initmodel()
            shape = subgrid.get_var_shape('s1')
            self.assertGreater(shape[0], 10)

    @printname
    def test_get_nd(self):
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            subgrid.initmodel()
            arr = subgrid.get_nd('s1')
            self.assertEqual(len(arr.shape), 1)
            logging.debug(arr)

    @printname
    def test_get_sharedmem(self):
        import multiprocessing
        import time

        with SubgridWrapper(
                mdu=self._mdu_path('1dpumps'), sharedmem=True) as subgrid:
            subgrid.initmodel()

            q = multiprocessing.Queue()

            def update_s1():
                q.put(subgrid.get_nd('s1'))

            p1 = multiprocessing.Process(target=update_s1)

            # Get initial water level
            s0 = subgrid.get_nd('s1')

            # Start subprocess
            p1.start()
            # Wait for process to put array in queue
            time.sleep(1)
            # Start updating
            subgrid.update(-1)
            # Wait for process to finish
            p1.join()
            # Get the array
            s1 = q.get()
            # Get the new array, which should now be changed
            s2 = subgrid.get_nd('s1')
            self.assertEqual(s0.sum(), s1.sum())
            # breaks if 1d is broken
            self.assertNotEqual(s1.sum(), s2.sum())

    @printname
    def test_nd_t1(self):
        with SubgridWrapper(mdu=self._mdu_path('hhnk')) as subgrid:
            subgrid.initmodel()
            subgrid.update(-1)
            subgrid.update(-1)
            subgrid.update(-1)
            subgrid.update(-1)
            subgrid.update(-1)
            t1 = subgrid.get_nd('t1')
            logging.debug(t1)
            self.assertTrue(float_equals(t1, 300))

    @printname
    def test_get_nd_unknown_variable(self):
        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            subgrid.initmodel()
            self.assertRaises(NotDocumentedError, subgrid.get_nd, 'reinout')

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
    def test_changebathy(self):

        with SubgridWrapper(mdu=self.default_mdu) as subgrid:
            for i in range(5):
                subgrid.update(-1)  # -1 = use default model time

            xc = 250808.205511
            yc = 589490.224168
            sz = 15
            bval = -11.23
            bmode = 0  # 0 = relative, 1 = absolute

            subgrid.changebathy(xc, yc, sz, bval, bmode)

            bval = 5
            bmode = 1  # 0 = relative, 1 = absolute

            subgrid.changebathy(xc, yc, sz, bval, bmode)

            for i in range(5):
                subgrid.update(-1)  # -1 = use default model time

    @printname
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

    @printname
    def test_link_table(self):
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            data = dict(branch=subgrid.get_nd('link_branchid'),
                        chainage=subgrid.get_nd('link_chainage'),
                        idx=subgrid.get_nd('link_idx'))
            df = pandas.DataFrame(data)
            for counter, branch_id in enumerate(data['branch']):
                print('branch id %d -> flowlink %d' %
                    branch_id, data['idx'][counter])
            self.assertEqual(df.idx.item(0), 249)
            self.assertEqual(df.idx.item(-1), 248)

    @printname
    def test_link_table_node(self):
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            data = dict(branch=subgrid.get_nd('nod_branchid'),
                        # ^^^ node number in inp file
                        chainage=subgrid.get_nd('nod_chainage'),
                        # ^^^ node number in nflowlink dimension (?)
                        idx=subgrid.get_nd('nod_idx'))
            # df = pandas.DataFrame(data)
            for counter, branch_id in enumerate(data['branch']):
                print('branch id %d -> flowelem %d' %
                    branch_id, data['idx'][counter])
            #self.assertEqual(df.idx.item(0), 249)
            #self.assertEqual(df.idx.item(-1), 248)
        # TODO: look up real indices for this test case

    @printname
    def test_flow_link(self):
        with SubgridWrapper(mdu=self._mdu_path('1d-democase')) as subgrid:
            flow_link = subgrid.get_nd('FlowLink')
            self.assertEqual(list(flow_link[249]), [140, 169])

    @printname
    def test_floodfill(self):
        with SubgridWrapper(mdu=self._mdu_path('betondorp')) as subgrid:

            x = 125176.875732
            y = 483812.708018
            level = -1.00
            mode = 1

            subgrid.floodfilling(x, y, level, mode)

            x = 125176.875732
            y = 483812.708018
            level = -0.80
            mode = 1

            subgrid.floodfilling(x, y, level, mode)

            x = 125176.875732
            y = 483812.708018
            level = -0.60
            mode = 1

            subgrid.floodfilling(x, y, level, mode)

            x = 125176.875732
            y = 483812.708018
            level = -0.40
            mode = 1

            subgrid.floodfilling(x, y, level, mode)

            x = 125176.875732
            y = 483812.708018
            level = 0.20
            mode = 1

            subgrid.floodfilling(x, y, level, mode)

    #
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

    @printname
    def test_s1(self):
        with SubgridWrapper(mdu=self._mdu_path('brouwersdam')) as subgrid:
            s1 = subgrid.get_nd('s1').copy()

    @printname
    def test_link_value(self):
        with SubgridWrapper(mdu=self._mdu_path('brouwersdam')) as subgrid:
            q = subgrid.get_nd('q').copy()
            print(q[1245])


# For Martijn
if __name__ == '__main__':
    unittest.main()
