import multiprocessing
import io
import logging
import threading

import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import zmq
import zmq.eventloop.zmqstream

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from flask import Flask, g, Response
from flask import _app_ctx_stack as stack


app = Flask(__name__)
logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)

def recv_array(socket, flags=0, copy=False, track=False):
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = buffer(msg)
    A = np.frombuffer(buf, dtype=md['dtype'])
    A.reshape(md['shape'])
    return A, md


@app.route("/img")
def render():
    ctx.sc.set_array(ctx.g.data["s1"][1:-2])
    ctx.ax.autoscale()
    stream = io.BytesIO()
    ctx.canvas.draw()
    ctx.canvas.print_png(stream)
    response = Response(stream.getvalue(), content_type="image/png")
    return response

@app.route("/")
def index():
    return """
    <img src="/img" id="img">
    <script>
setInterval(function() {
    var img = document.getElementById('img');
    img.src = '/img?rand=' + Math.random();
}, 200);
    </script>
    """


def model_listener(ctx):
    """keep pushing data to main context"""
    while True:
        data, metadata = recv_array(socket)
        ctx.g.data[metadata['name']] = data
        ctx.push()


if __name__ == '__main__':

    # push it into the application context


    logger.info("Connecting to grid")
    zmqctx = zmq.Context()
    reqsock = zmqctx.socket(zmq.REQ)
    reqsock.connect("tcp://localhost:5557")
    reqsock.send("yo give me the grid")
    grid = reqsock.recv_pyobj()

    logger.info("Share grid with WMS")


    logger = logging.getLogger("listener")
    logger.setLevel(logging.INFO)

    logger.info("Subscribe to model updates")
    zmqctx = zmq.Context()
    subsock = zmqctx.socket(zmq.SUB)
    subsock.connect("tcp://localhost:5556")
    subsock.setsockopt(zmq.SUBSCRIBE,'')


    with app.app_context() as ctx:
        ctx.g.grid = grid
        ctx.g.data = {}
        ctx.fig = Figure()
        ctx.canvas = FigureCanvas(ctx.fig)
        ctx.ax = ctx.fig.add_subplot(111)
        ctx.sc = ctx.ax.scatter(g.grid["FlowElem_xcc"][1:-2], g.grid["FlowElem_ycc"][1:-2], c=np.zeros_like(g.grid["FlowElem_ycc"][1:-2]), vmin=0, vmax=3)
        ctx.push()


        logger.info("Starting listener")
        thread = threading.Thread(target=model_listener, args=[ctx])
        thread.start()
    app.run(port=6001)
    logger.info("Starting servers")
    # memory address


