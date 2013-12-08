"""
Subgrid socket server
"""
from python_subgrid.wrapper import SubgridWrapper, logger
from python_subgrid.wrapper import DOCUMENTED_VARIABLES


import pdb
import time
import os
import io
import numpy as np
import multiprocessing
import ctypes
import json

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


from flask import Flask, g, Response
app = Flask(__name__)



@app.route("/")
def render():
    s1 = np.frombuffer(g.shared_arr.get_obj())
    response = Response(json.dumps({'s1': s1.tolist()}), mimetype='application/json')

    # # this hangs in parallel blas for me....
    # from matplotlib.figure import Figure
    # from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

    # fig = Figure()
    # canvas = FigureCanvas(fig)
    # ax = fig.add_subplot(111)
    # stream = io.BytesIO()
    # canvas.print_png(stream)

    return response

scenarios = {
    '1dpumps': {
        'path': '1dpumptest',
        'mdu_filename': "1d2d_kunstw.mdu",
    },
    'DelflandiPad': {
        'path': 'delfland-model-voor-3di',
        'mdu_filename': "hhdlipad.mdu",
    },
    'hhnk': {
        'path': 'hhnkipad',
        'mdu_filename': "HHNKiPad.mdu",
    }}
scenario = 'DelflandiPad'
#scenario = '1dpumps'

scenario_basedir = os.path.abspath(os.environ['SCENARIO_BASEDIR'])
abs_path = os.path.join(scenario_basedir,
                        scenarios[scenario]['path'], scenarios[scenario]['mdu_filename'])


def wms_process(app, port):
    """Main wms boss supervisor thingy"""
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port)
    IOLoop.instance().start()
    # as we're already forked we can just run the flask app directly I think....
    # app.run(port=port)


if __name__ == '__main__':

    with SubgridWrapper(mdu=abs_path) as subgrid:

        ctx = app.app_context()

        subgrid.initmodel()

        s1 = subgrid.get_nd('s1')

        # Create a block of shared memory
        # Since multiprocessing is forking we need a separate shared memory array
        shared_arr = multiprocessing.Array(ctypes.c_double, s1.shape[0])

        # push it into the application context
        ctx.g.shared_arr = shared_arr
        ctx.push()

        for port in range(6500, 6504):
            # memory address
            process = multiprocessing.Process(target=wms_process, args=[app, port])
            process.start()
        while True:
            # Calculate
            subgrid.update(-1)
            # Get a new s1
            s1 = subgrid.get_nd('s1')
            # Update the shared memory
            shared_arr[:] = s1[:]
            # Wait a bit
            time.sleep(1)

