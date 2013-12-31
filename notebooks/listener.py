import zmq

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

ctx = zmq.Context()
subsock = ctx.socket(zmq.SUB)
subsock.connect("tcp://localhost:5556")
subsock.setsockopt(zmq.SUBSCRIBE,'')

reqsock = ctx.socket(zmq.REQ)
reqsock.connect("tcp://localhost:5557")
reqsock.send("yo give me the grid")
grid = reqsock.recv_pyobj()


fig, ax = plt.subplots()

sc = ax.scatter(grid['FlowElem_xcc'][1:-2], grid['FlowElem_ycc'][1:-2], c=np.zeros_like(grid["FlowElem_xcc"][1:-2]), vmin=0, vmax=3)
plt.colorbar(sc, ax=ax)
while True:
    obj = subsock.recv_pyobj()
    if "s1" in obj:
        sc.set_array(obj['s1'][1:-2])
        ax.autoscale()
        plt.draw()
