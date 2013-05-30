"""
Test the library on desired behavior by running it on several models.
"""
import unittest
import os
import ctypes

from python_subgrid.wrapper import subgrid
# from numpy.ctypeslib import ndpointer


EPSILON = 0.00000001

scenarios = {
    'DelflandiPad': {
        'name': 'Delfland',
        'path': 'DelflandiPad',
        'mdu_filename': "DelflandiPad.mdu",
        'asc_filename': 'ahn_guts_v4.asc'  # TODO: read from mdu
    },
    'hunzeenaas': {
        'name': 'Hunze en Aas',
        'path': 'hunzeenaas',
        'mdu_filename': "hunzeenaas.mdu",
        'asc_filename': 'h25m.asc'  # TODO: read from mdu
    },
    'betondorp': {
        'name': 'Betondorp',
        'path': 'betondorp',
        'mdu_filename': "betondorp.mdu",
        'asc_filename': 'betondorp_selectie2.asc'  # TODO: read from mdu
    },
}
DEFAULT_SCENARIO = 'DelflandiPad'

# By default, we look for scenario dirs in the current working directory. This
# means you need to create symlinks to them. An alternative is to set the
# SCENARIO_BASEDIR environment variable.
scenario_basedir = os.getcwd()
if 'SCENARIO_BASEDIR' in os.environ:
    scenario_basedir = os.path.abspath(os.environ['SCENARIO_BASEDIR'])
print 'Scenario base dir: %s' % scenario_basedir


def load_model(path, mdu_filename):
    os.chdir(path)
    #mdu_filename_20 = '%-20s' % mdu_filename
    mdu_string_buffer = ctypes.create_string_buffer(mdu_filename)
    #ierr = libsubgrid.funcall('loadmodel', "args[1]", mdu_string_buffer)
    ierr = subgrid.loadmodel(mdu_string_buffer)
    if ierr != 0:
        print 'ERROR!'
        # TODO: Jack: raise exception, or something else?


class LibSubgridTest(unittest.TestCase):

    def setUp(self):
        #libsubgrid.funcall('startup')
        self.startdir = os.getcwd()
        subgrid.startup()
        self.model_initialized = False

    def tearDown(self):
        if self.model_initialized:
            subgrid.finalizemodel()
        subgrid.shutdown()
        os.chdir(self.startdir)

    def test_info(self):
        print subgrid.subgrid_info()

    def test_load(self):
        print
        print '########### test load'
        for i in xrange(3):
            print 'test load %r' % i
            abs_path = os.path.join(scenario_basedir,
                                    scenarios[DEFAULT_SCENARIO]['path'])
            load_model(abs_path, scenarios[DEFAULT_SCENARIO]['mdu_filename'])
            subgrid.initmodel()
            subgrid.finalizemodel()  # Need to finalize before re-initializing

    def test_init(self):
        print
        print '########### test init: we try to initialize multiple times'
        abs_path = os.path.join(scenario_basedir,
                                scenarios[DEFAULT_SCENARIO]['path'])
        load_model(abs_path, scenarios[DEFAULT_SCENARIO]['mdu_filename'])
        for i in xrange(3):
            print 'test initmodel %r' % i
            subgrid.initmodel()
        self.model_initialized = True

    # def test_arraypointer(self):
    #     """"arrays: see bmi.py:get_nd, get , set / rank, shape, type"""
    #     print
    #     print '########### test array pointer'
    #     import numpy as np
    #     a = ndpointer(
    #         dtype='double', ndim=3, shape=(2,3,4), flags='F')

    #     subgrid.subgrid_arraypointer(ctypes.byref(a))
    #     print np.reshape(np.asarray(a).ravel(), [2,3,4], order='F')
    #     """
    #     [[[ 1.  1.  1.  1.]
    #     [ 1.  1.  1.  1.]
    #     [ 1.  1.  1.  1.]]

    #     [[ 2.  2.  2.  2.]
    #     [ 2.  2.  2.  2.]
    #     [ 2.  2.  2.  2.]]]
    #     """

    def test_timesteps(self):
        print
        print '########### test timesteps'
        abs_path = os.path.join(scenario_basedir,
                                scenarios[DEFAULT_SCENARIO]['path'])
        load_model(abs_path, scenarios[DEFAULT_SCENARIO]['mdu_filename'])
        subgrid.initmodel()
        self.model_initialized = True

        for i in xrange(10):
            print 'doing %d...' % i
            # print libsubgrid.funcall(
            #     'update',
            #     'ctypes.byref(ctypes.c_double(-1))')
            print subgrid.update(ctypes.c_double(-1))
            # -1 = use default model timestep.

        #libsubgrid.funcall('finalizemodel')

    def xtest_manhole(self):
        print
        print '############ test manhole'
        abs_path = os.path.join(scenario_basedir,
                                scenarios[DEFAULT_SCENARIO]['path'])
        load_model(abs_path, scenarios[DEFAULT_SCENARIO]['mdu_filename'])
        subgrid.initmodel()
        self.model_initialized = True

        manhole_name = ctypes.create_string_buffer('test_manhole')
        x = ctypes.c_double(85830.97071920538)
        y = ctypes.c_double(448605.8983910042)
        discharge_value = ctypes.c_double(100.0)
        itype = ctypes.c_int(1)
        #subgrid.discharge(x, y, manhole_name, itype, discharge_value)
        subgrid.discharge(85830.97071920538, 448605.8983910042, manhole_name, 1, 100.0)

    # def test_get_water_level(self):
    #     print
    #     print '########### test get water level'
    #     abs_path = os.path.join(scenario_basedir,
    #                             scenarios[DEFAULT_SCENARIO]['path'])
    #     load_model(abs_path, scenarios[DEFAULT_SCENARIO]['mdu_filename'])
    #     subgrid.initmodel()
    #     self.model_initialized = True

    #     for i in xrange(10):
    #         print 'doing %d...' % i
    #         #print libsubgrid.funcall('update',
    #                 'ctypes.byref(ctypes.c_double(-1))') # -1 = use default model timestep.
    #         print subgrid.update(-1) # -1 = use default model time
    #     level = ctypes.c_double(-1234.0)
    #     #level_p = ctypes.POINTER(0.0) #ctypes.c_double(0.0)
    #     xtest = ctypes.c_double(251929.987738)
    #     ytest = ctypes.c_double(589375.641241)

    #     result = subgrid.getwaterlevel(
    #         ctypes.byref(xtest),
    #         ctypes.byref(ytest),
    #         ctypes.byref(level)
    #     )
    #     # result = libsubgrid.funcall(
    #     #     'GETWATERLEVEL',
    #     #     'ctypes.byref(args[1]), ctypes.byref(args[2]), ctypes.byref(args[3])',
    #     #     xtest, ytest, level)
    #     print "na getwaterlevel, result at (%r, %r): %r" % (xtest, ytest, level)
    #     print 'true? %r' % (abs(level.value - -1.6409107876960418) < EPSILON)
    #     # The value is -999 now..
    #     #unittest.assertTrue((level.value - -1.6409107876960418) < EPSILON)

    #     for i in xrange(10):
    #         print 'doing %d...' % i
    #         print subgrid.update(-1) # -1 = use default model time
    #         # print libsubgrid.funcall(
    #         #     'update', 'ctypes.byref(ctypes.c_double(-1))') # -1 = use default model timestep.

    #     result = subgrid.getwaterlevel(
    #         ctypes.byref(xtest),
    #         ctypes.byref(ytest),
    #         ctypes.byref(level)
    #     )

    #     # result = libsubgrid.funcall(
    #     #     'GETWATERLEVEL',
    #     #     'ctypes.byref(args[1]), ctypes.byref(args[2]), ctypes.byref(args[3])',
    #     #     xtest, ytest, level)
    #     print "na getwaterlevel2, result at (%r, %r): %r" % (xtest, ytest, level)
    #     # After one run it has this value... don't know if we have to check,
    #     # but it's a got change follower
    #     # The value is -999 now..
    #     print 'true? %r' % (abs(level.value - -1.4157227881505232) < EPSILON)
    #     print 'true? %r' % (abs(level.value - -1.2157227881505232) < EPSILON)
    #     #unittest.assertTrue((level.value - -1.4157227881505232) < EPSILON)

    #     #libsubgrid.funcall('finalizemodel')


    # def test_changebathy(self):
    #     print
    #     print '########### test change bathy'
    #     abs_path = os.path.join(scenario_basedir, scenarios[DEFAULT_SCENARIO]['path'])
    #     load_model(abs_path, scenarios[DEFAULT_SCENARIO]['mdu_filename'])
    #     subgrid.initmodel()
    #     self.model_initialized = True

    #     for i in xrange(10):
    #         print 'doing %d...' % i
    #         print subgrid.update(-1) # -1 = use default model time

    #     xc = 250808.205511
    #     yc = 589490.224168
    #     sz = 15
    #     bval = -11.23
    #     bmode = 0

    #     subgrid.changebathy(xc, yc, sz, bval, bmode)

    #     # libsubgrid.funcall(
    #     #     'changebathy',
    #     #     'ctypes.c_double(args[1]), ctypes.c_double(args[2]), ctypes.c_double(args[3]), ctypes.c_double(args[4]), ctypes.c_int(args[5])',
    #     #     xc, yc, sz, bval, bmode)

    #     #libsubgrid.funcall('finalizemodel')

    # # def test_changebathy2(self):
    # #     """Known crashing case"""
    # #     print
    # #     print '########### test change bathy2'
    # #     abs_path = os.path.join(scenario_basedir, scenarios['betondorp']['path'])
    # #     load_model(abs_path, scenarios['betondorp']['mdu_filename'])
    # #     libsubgrid.funcall('initmodel')
    # #     self.model_initialized = True

    # #     xc = 125209.332
    # #     yc = 483799.384
    # #     sz = 50.000
    # #     bval = -3.000
    # #     bmode = 0

    # #     libsubgrid.funcall(
    # #         'changebathy',
    # #         'ctypes.c_double(args[1]), ctypes.c_double(args[2]), ctypes.c_double(args[3]), ctypes.c_double(args[4]), ctypes.c_int(args[5])',
    # #         xc, yc, sz, bval, bmode)
    # #     #libsubgrid.funcall('finalizemodel')

    def xtest_floodfill(self):
        print
        print '########### test floodfill'
        abs_path = os.path.join(scenario_basedir,
                                scenarios['betondorp']['path'])
        load_model(abs_path, scenarios['betondorp']['mdu_filename'])
        subgrid.initmodel()
        self.model_initialized = True

        x = ctypes.c_double(125176.875732)
        y = ctypes.c_double(483812.708018)
        level = ctypes.c_double(-1.00)
        mode = ctypes.c_int(1)

        # libsubgrid.funcall(
        #     'floodfilling',
        #     'ctypes.byref(args[1]), ctypes.byref(args[2]), ctypes.byref(args[3]), ctypes.byref(args[4])',
        #     x, y, level, mode)
        subgrid.floodfilling(
            ctypes.byref(x), ctypes.byref(y), ctypes.byref(level),
            ctypes.byref(mode))

        x = ctypes.c_double(125176.875732)
        y = ctypes.c_double(483812.708018)
        level = ctypes.c_double(-0.80)
        mode = ctypes.c_int(1)

        subgrid.floodfilling(
            ctypes.byref(x), ctypes.byref(y), ctypes.byref(level),
            ctypes.byref(mode))

        x = ctypes.c_double(125176.875732)
        y = ctypes.c_double(483812.708018)
        level = ctypes.c_double(-0.60)
        mode = ctypes.c_int(1)

        subgrid.floodfilling(
            ctypes.byref(x), ctypes.byref(y), ctypes.byref(level),
            ctypes.byref(mode))

        x = ctypes.c_double(125176.875732)
        y = ctypes.c_double(483812.708018)
        level = ctypes.c_double(-0.40)
        mode = ctypes.c_int(1)

        subgrid.floodfilling(
            ctypes.byref(x), ctypes.byref(y), ctypes.byref(level),
            ctypes.byref(mode))

        x = ctypes.c_double(125176.875732)
        y = ctypes.c_double(483812.708018)
        level = ctypes.c_double(-0.20)
        mode = ctypes.c_int(1)

        subgrid.floodfilling(
            ctypes.byref(x), ctypes.byref(y), ctypes.byref(level),
            ctypes.byref(mode))

        #libsubgrid.funcall('finalizemodel')
        self.model_initialized = True

    # # def test_floodfill2(self):
    # #     print
    # #     print '########### test floodfill'
    # #     abs_path = os.path.join('/home/user/3di/Case Hillegersberg')
    # #     load_model(abs_path, 'Hillegersberg.mdu')
    # #     libsubgrid.funcall('initmodel')
    # #     self.model_initialized = True

    # #     x = ctypes.c_double(89022.231659)
    # #     y = ctypes.c_double(440488.157517)
    # #     level = ctypes.c_double(1.0)
    # #     mode = ctypes.c_int(0)

    # #     libsubgrid.funcall(
    # #         'floodfilling',
    # #         'ctypes.byref(args[1]), ctypes.byref(args[2]), ctypes.byref(args[3]), ctypes.byref(args[4])',
    # #         x, y, level, mode)

    # #     x = ctypes.c_double(89308.862230)
    # #     y = ctypes.c_double(440743.378386)
    # #     level = ctypes.c_double(1.0)
    # #     mode = ctypes.c_int(0)

    # #     libsubgrid.funcall(
    # #     'floodfilling',
    # #     'ctypes.byref(args[1]), ctypes.byref(args[2]), ctypes.byref(args[3]), ctypes.byref(args[4])',
    # #     x, y, level, mode)

    # #     # x = ctypes.c_double(125176.875732)
    # #     # y = ctypes.c_double(483812.708018)
    # #     # level = ctypes.c_double(-0.60)
    # #     # mode = ctypes.c_int(1)

    # #     # libsubgrid.funcall(
    # #     #     'floodfilling',
    # #     #     'ctypes.byref(args[1]), ctypes.byref(args[2]), ctypes.byref(args[3]), ctypes.byref(args[4])',
    # #     #     x, y, level, mode)

    # #     # x = ctypes.c_double(125176.875732)
    # #     # y = ctypes.c_double(483812.708018)
    # #     # level = ctypes.c_double(-0.40)
    # #     # mode = ctypes.c_int(1)

    # #     # libsubgrid.funcall(
    # #     #     'floodfilling',
    # #     #     'ctypes.byref(args[1]), ctypes.byref(args[2]), ctypes.byref(args[3]), ctypes.byref(args[4])',
    # #     #     x, y, level, mode)

    # #     # x = ctypes.c_double(125176.875732)
    # #     # y = ctypes.c_double(483812.708018)
    # #     # level = ctypes.c_double(-0.20)
    # #     # mode = ctypes.c_int(1)

    # #     # libsubgrid.funcall(
    # #     #     'floodfilling',
    # #     #     'ctypes.byref(args[1]), ctypes.byref(args[2]), ctypes.byref(args[3]), ctypes.byref(args[4])',
    # #     #     x, y, level, mode)

    # #     #libsubgrid.funcall('finalizemodel')
