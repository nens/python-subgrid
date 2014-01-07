import logging
import zmq

import datetime
import dateutil.parser
import numpy as np

def recv_array(socket, flags=0, copy=False, track=False):
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = buffer(msg)
    A = np.frombuffer(buf, dtype=md['dtype'])
    A.reshape(md['shape'])
    return A, md


logging.basicConfig()
logger = logging.getLogger("listener")
logger.setLevel(logging.INFO)


logger.info("Subscribe to model updates")

zmqctx = zmq.Context()
subsock = zmqctx.socket(zmq.SUB)
subsock.connect("tcp://localhost:5556")
subsock.setsockopt(zmq.SUBSCRIBE,'')


while True:
    data, metadata = recv_array(subsock)
    logger.info("data contains {} {}".format(metadata, data.shape))
    if "send" in metadata:
        then = dateutil.parser.parse(metadata["send"])
        now = datetime.datetime.now()
        logger.info("received in {}".format(now - then))
