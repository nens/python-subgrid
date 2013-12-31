#!/usr/bin/env python

"""
subgrid model runner
"""
from python_subgrid.wrapper import SubgridWrapper
from multiprocessing import Process
import zmq
import zmq.eventloop.zmqstream
from zmq.eventloop import ioloop, zmqstream
ioloop.install()
import argparse

def parse_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-p', '--port', dest='port',
                                help='publishing port',
                                type=int,
                                default=5556)
    argparser.add_argument('-v', '--variables', dest='variables',
                           metavar='V',
                           nargs='*',
                           help='variables to be published',
                           default=[]
                       )
    argparser.add_argument('mdu',
                           help='model mdu file')
    return argparser.parse_args()


def make_rep_socket(port, data):
    """make a socket that replies to message with the grid"""

    context = zmq.Context()
    repsock = context.socket(zmq.REP)
    repsock.bind(
        "tcp://*:{port}".format(port=port)
    )
    repstream = zmqstream.ZMQStream(repsock)

    def respond(stream, msg):
        stream.send_pyobj(
            data
        )
    repstream.on_recv_stream(respond)
    # start listening to grid requests
    ioloop.IOLoop.instance().start()


# see or an in memory numpy message:
# http://zeromq.github.io/pyzmq/serialization.html
if __name__ == '__main__':

    arguments = parse_args()
    context = zmq.Context()

    # for sending messages
    pubsock = context.socket(zmq.PUB)
    pubsock.bind(
        "tcp://*:{port}".format(port=arguments.port)
    )

    # for replying to grid requests
    with SubgridWrapper(mdu=arguments.mdu, sharedmem=False) as subgrid:
        subgrid.initmodel()

        # Start a reply process in the background
        data = {
            'FlowElem_xcc': subgrid.get_nd('FlowElem_xcc').copy(),
            'FlowElem_ycc': subgrid.get_nd('FlowElem_ycc').copy(),
        }
        Process(target=make_rep_socket, args=(arguments.port + 1, data)).start()


        # reply with grid
        while True:
            # Calculate
            subgrid.update(-1)
            msg = {}
            for key in arguments.variables:
                value = subgrid.get_nd(key)
                # 4ms for 1M doubles
                msg[key] = value
            pubsock.send_pyobj(msg)

