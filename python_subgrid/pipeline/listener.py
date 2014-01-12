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

zmqctx = zmq.Context()


logger.info("Getting grid info")
reqsock = zmqctx.socket(zmq.REQ)
reqsock.connect("tcp://localhost:5556")
reqsock.send_pyobj("hi hi")
reply = reqsock.recv_pyobj()
logger.info("got back {}".format(reply))

logger.info("Subscribe to model updates")
subsock = zmqctx.socket(zmq.SUB)
subsock.connect("tcp://localhost:5558")
subsock.setsockopt(zmq.SUBSCRIBE,'')



while True:
    data, metadata = recv_array(subsock)
    logger.info("data contains {} {}".format(metadata, data.shape))
    if "timestamp" in metadata:
        then = dateutil.parser.parse(metadata["timestamp"])
        now = datetime.datetime.now()
        logger.info("received in {}".format(now - then))
