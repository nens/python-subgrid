import sys
import time


import websocket  # install by: pip install websocket-client


def main(address, url='publish', n=100):
    ws = websocket.create_connection('ws://{}/{}'.format(address, url))
    deltas = []
    print("Waiting for %d messages...".format(n))
    for i, msg in enumerate(ws):
        if i > n:
            # do n measurements
            break
        print(msg)
        # deltas.append(end - start)
    ws.close()
    # average = sum(deltas) / len(deltas)
    # print("sending 'hello world' took on average {} seconds (n={}).".format(average, n))

if __name__ == '__main__':
    address = '127.0.0.1:22222'  # default
    args = sys.argv
    if len(args) > 1:
        address = args[1]
    main(address)
