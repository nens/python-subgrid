#!/usr/bin/env python

"""
subgrid model runner
"""
from python_subgrid.wrapper import SubgridWrapper
from multiprocessing import Process
import zmq
import zmq.eventloop.zmqstream
from zmq.eventloop import ioloop, zmqstream

import datetime
import logging
logging.basicConfig()

logger = logging.getLogger(__name__)

ioloop.install()
import argparse


INITVARS = {'FlowElem_xcc', 'FlowElem_ycc', 'FlowElemContour_x', 'FlowElemContour_y', 'dx', 'nmax', 'mmax',
            'mbndry', 'nbndry', 'ip', 'jp', 'nodm', 'nodn', 'nodk', 'nod_type'}
OUTPUTVARS = ['s1']
def send_array(socket, A, flags=0, copy=False, track=False, metadata=None):
    """send a numpy array with metadata"""
    md = dict(
        dtype = str(A.dtype),
        shape = A.shape,
        send = datetime.datetime.now().isoformat()
    )
    if metadata:
        md.update(metadata)
    socket.send_json(md, flags|zmq.SNDMORE)
    msg = buffer(A)
    socket.send(msg, flags, copy=copy, track=track)
    return

def parse_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-p', '--publishport', dest='publish_port',
                                help='publishing port (port that publishes model results)',
                                type=int,
                                default=5556)
    argparser.add_argument('-r', '--replyport', dest='reply_port',
                           help='reply port (port which responds to requests)',
                           type=int,
                           default=5557)
    argparser.add_argument('-n', '--interval', dest='interval',
                           help='publishing results every [n] tiemsteps',
                           type=int,
                           default=10)
    argparser.add_argument('-o', '--outputvariables', dest='outputvariables',
                           metavar='O',
                           nargs='*',
                           help='variables to be published',
                           default=OUTPUTVARS
                       )
    argparser.add_argument('-g', '--global', dest='globalvariables',
                           metavar='G',
                           nargs='*',
                           help='variables that can be send back to a reply (not changed during run)',
                           default=INITVARS
    )
    argparser.add_argument('-c', '--config', dest='config',
                           help='configuration file',
                           default=None
    )
    argparser.add_argument('ini',
                           help='model configuration file')
    argparser.add_argument("-s", "--serialization",
                           dest="serialization protocol (numpy, json, bytes)",
                           default="numpy"
                       )
    return argparser.parse_args()


def make_rep_socket(port, data):
    """make a socket that replies to message with the grid"""

    context = zmq.Context()
    repsock = context.socket(zmq.REP)
    repsock.bind(
        "tcp://*:{port}".format(port=port)
    )

    #  TODO handle update messages here
    # do we need to pass ioloop here?
    repstream = zmqstream.ZMQStream(repsock)

    def respond(stream, msg):
        stream.send_pyobj(
            data
        )
    repstream.on_recv_stream(respond)
    # start listening to grid requests
    ioloop.IOLoop.instance().start()

def make_pub_socket(port):
    context = zmq.Context()

    # for sending messages
    pubsock = context.socket(zmq.PUB)
    pubsock.bind(
        "tcp://*:{port}".format(port=port)
    )
    return pubsock
# see or an in memory numpy message:
# http://zeromq.github.io/pyzmq/serialization.html


if __name__ == '__main__':

    arguments = parse_args()


    # for replying to grid requests
    with SubgridWrapper(mdu=arguments.ini, sharedmem=False) as subgrid:
        subgrid.initmodel()

        # Start a reply process in the background, with variables available
        # after initialization, sent all at once as py_obj
        data = {
            var: subgrid.get_nd(var)
            for var
            in arguments.globalvariables
        }

        Process(target=make_rep_socket, args=(arguments.reply_port, data)).start()
        pubsock = make_pub_socket(port=arguments.publish_port)

        i = 0
        while True:
            # Calculate
            subgrid.update(-1)

            i+=1
            # not on an interval
            if (i % arguments.interval):
                continue
            for key in arguments.outputvariables:
                value = subgrid.get_nd(key)
                metadata = {'name': key, 'iteration': i}
                # 4ms for 1M doubles
                logger.info("sending {}".format(metadata))
                send_array(pubsock, value, metadata=metadata)
