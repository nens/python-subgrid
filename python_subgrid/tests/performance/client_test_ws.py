import sys
import time


import websocket  # install by: pip install websocket-client


def main(address, url='ws', n=100):
    ws = websocket.create_connection('ws://{}/{}'.format(address, url))
    deltas = []
    print("sending 'hello world' over websocket {} times...".format(n))
    for i in range(n + 1):
        start = time.time()
        ws.send('hello world')
        end = time.time()
        deltas.append(end - start)
    ws.close()
    average = sum(deltas) / len(deltas)
    print("sending 'hello world' took on average {} seconds (n={}).".format(
        average, n))

if __name__ == '__main__':
    address = '127.0.0.1:8080'  # default
    args = sys.argv
    if len(args) > 1:
        address = args[1]
    main(address)

