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
    'testcase': {
        'path': 'testcase',
        'mdu_filename': 'testcase.mdu',
    }
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
