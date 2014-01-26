#!/usr/bin/env python

"""
subgrid model runner
"""
import datetime
import logging
import itertools
import argparse

import zmq
import zmq.eventloop.zmqstream
from zmq.eventloop import ioloop
import numpy as np

import python_subgrid.wrapper
import python_subgrid.plotting


logging.basicConfig()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ioloop.install()


INITVARS = {'FlowElem_xcc', 'FlowElem_ycc', 'FlowElemContour_x',
            'FlowElemContour_y', 'dx', 'nmax', 'mmax',
            'mbndry', 'nbndry', 'ip', 'jp', 'nodm', 'nodn', 'nodk', 'nod_type',
            'dps', 'x0p', 'y0p', 'dxp', 'dyp'}
OUTPUTVARS = ['s1']


def send_array(socket, A, flags=0, copy=False, track=False, metadata=None):
    """send a numpy array with metadata"""
    md = dict(
        dtype=str(A.dtype),
        shape=A.shape,
        timestamp=datetime.datetime.now().isoformat()
    )
    if metadata:
        md.update(metadata)
    socket.send_json(md, flags | zmq.SNDMORE)
    msg = buffer(A)
    socket.send(msg, flags, copy=copy, track=track)
    return


def recv_array(socket, flags=0, copy=False, track=False):
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = buffer(msg)
    A = np.frombuffer(buf, dtype=md['dtype'])
    A.reshape(md['shape'])
    return A, md


def parse_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '-p', '--publishport', dest='publish_port',
        help='publishing port (port that publishes model results)',
        type=int,
        default=5556)
    argparser.add_argument(
        '-r', '--replyport', dest='reply_port',
        help='reply port (port which responds to requests)',
        type=int,
        default=5557)
    argparser.add_argument(
        '-n', '--interval', dest='interval',
        help='publishing results every [n] tiemsteps',
        type=int,
        default=1)
    argparser.add_argument(
        '-o', '--outputvariables', dest='outputvariables',
        metavar='O',
        nargs='*',
        help='variables to be published',
        default=OUTPUTVARS)
    argparser.add_argument(
        '-g', '--global', dest='globalvariables',
        metavar='G',
        nargs='*',
        help='variables that can be send back to a reply (not changed during run)',
        default=INITVARS)
    argparser.add_argument(
        '-c', '--config', dest='config',
        help='configuration file',
        default=None)
    argparser.add_argument(
        'ini',
        help='model configuration file')
    argparser.add_argument(
        "-s", "--serialization",
        dest="serialization protocol (numpy, json, bytes)",
        default="numpy")
    return argparser.parse_args()


# see or an in memory numpy message:
# http://zeromq.github.io/pyzmq/serialization.html


def process_incoming(subgrid, poller, rep, pull, data):
    """
    process incoming messages
    """
    # Check for new messages
    items = poller.poll(100)
    for sock, n in items:
        for i in range(n):
            if sock == rep:
                logger.info("got reply message, reading")
                msg = sock.recv()
                logger.info("got message: {}, replying with data".format(msg))
                sock.send_pyobj(data)
                logger.info("sent".format(msg))
            elif sock == pull:
                logger.info("got push message(s), reducing")
                data, metadata = recv_array(sock)
                logger.info("got metadata: %s", metadata)
                if "action" in metadata:
                    logger.info("found action applying update")
                    # TODO: support same operators as MPI_ops here....,
                    # TODO: reduce before apply
                    action = metadata['action']
                    arr = subgrid.get_nd(metadata['name'])
                    S = tuple(slice(*x) for x in action['slice'])
                    print(repr(arr[S]))
                    if action['operator'] == 'setitem':
                        arr[S] = data
                    elif action['operator'] == 'add':
                        arr[S] += data

            else:
                logger.warn("got message from unknown socket {}".format(sock))
    else:
        logger.info("No incoming data")

if __name__ == '__main__':

    arguments = parse_args()

    # make a socket that replies to message with the grid

    context = zmq.Context()
    # Socket to handle init data
    rep = context.socket(zmq.REP)
    rep.bind(
        "tcp://*:{port}".format(port=5556)
    )
    pull = context.socket(zmq.PULL)
    pull.connect(
        "tcp://localhost:{port}".format(port=5557)
    )
    # for sending model messages
    pub = context.socket(zmq.PUB)
    pub.bind(
        "tcp://*:{port}".format(port=5558)
    )

    poller = zmq.Poller()
    poller.register(rep, zmq.POLLIN)
    poller.register(pull, zmq.POLLIN)

    python_subgrid.wrapper.logger.setLevel(logging.WARN)

    # for replying to grid requests
    with python_subgrid.wrapper.SubgridWrapper(mdu=arguments.ini) as subgrid:
        subgrid.initmodel()

        # Start a reply process in the background, with variables available
        # after initialization, sent all at once as py_obj
        data = {
            var: subgrid.get_nd(var)
            for var
            in arguments.globalvariables
        }
        # add the quad_grid for easy plotting
        data["quad_grid"] = python_subgrid.plotting.make_quad_grid(subgrid)
        process_incoming(subgrid, poller, rep, pull, data)

        # Keep on counting indefinitely
        counter = itertools.count()

        for i in counter:

            # Any requests?
            process_incoming(subgrid, poller, rep, pull, data)

            # Calculate
            subgrid.update(-1)

            # check counter
            if (i % arguments.interval):
                continue

            for key in arguments.outputvariables:
                value = subgrid.get_nd(key)
                metadata = {'name': key, 'iteration': i}
                # 4ms for 1M doubles
                logger.info("sending {}".format(metadata))
                send_array(pub, value, metadata=metadata)
