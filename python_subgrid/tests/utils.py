import psutil
from functools import wraps
import logging

def colorlogs():
    try:
        from rainbow_logging_handler import RainbowLoggingHandler
        import sys
        # setup `RainbowLoggingHandler`
        logger = logging.root
        formatter = logging.Formatter("[%(asctime)s] %(name)s %(funcName)s():%(lineno)d\t%(message)s")  # same as default
        handler = RainbowLoggingHandler(sys.stderr, color_funcName=('black', 'gray', True))
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except ImportError:
        # rainbow logger not found, that's ok
        pass


def printinfo(f):
    """print info of the being called"""
    # needed because it does not show up if the test segfaults
    # this can probably be done easier
    @wraps(f)
    def wrapper(*args, **kwds):
        print("### running test {f}".format(f=f))
        print("available physical memory before {}".format(psutil.virtual_memory()))
        print("available swap memory before {}".format(psutil.swap_memory()))
        result = f(*args, **kwds)
        print("available physical memory after {}".format(psutil.virtual_memory()))
        print("available swap memory after {}".format(psutil.swap_memory()))

        return result
    return wrapper


scenarios = {
    '1dpumps': {
        'path': '1dpumptest',
        'mdu_filename': "1d2d_kunstw.mdu",
    },
    '1d-democase': {
        'path': '1d-democase',
        'mdu_filename': "1D-democase.mdu",
    },
    'testcase': {
        'path': 'testcase',
        'mdu_filename': "testcase_testcase.mdu",
    },
    'wijdewormer': {
        'path': 'wijdewormer_spatiallite',
        'mdu_filename': "wijdewormer_spatiallite.mdu",
    },
    'DelflandiPad': {
        'path': 'delfland-model-voor-3di',
        'mdu_filename': "hhdlipad.mdu",
    },
    'delfland_gebiedsbreed': {
        'path': 'delfland_gebiedsbreed',
        'mdu_filename': 'delfland_gebiedsbreed.mdu'
    },
    'delfland_gebiedsbreed2': {
        'path': 'delfland-gebiedsbreed',
        'mdu_filename': 'delfland_gebiedsbreed.mdu'
    },
    'duifpolder_slice': {
        'path': 'duifpolder_slice',
        'mdu_filename': 'duifpolder_slice_duif_slice.mdu'
    },
    'hhnk_gebiedsbreed': {
        'path': 'hhnk_gebiedsbreed',
        'mdu_filename': 'hhnk_hhnk.mdu'
    },
    'hhnk': {
        'path': 'hhnkipad',
        'mdu_filename': "HHNKiPad.mdu",
    },
    'hhnk_gebiedsbreed': {
        'path': 'hhnk_gebiedsbreed',
        'mdu_filename': "hhnk_hhnk.mdu",
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
    'duifpolder_slice':{
        'path': 'duifpolder_slice',
        'mdu_filename': 'duifpolder_slice_duif_slice.mdu'
    },
    'duifpolder_2d':{
        'path': 'duifpolder_slice',
        'mdu_filename': 'duifpolder_slice_duif_slice_only2d.mdu'
    },
}

