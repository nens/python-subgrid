#!/usr/bin/env python
import logging
import threading
import time
import json
import datetime
import itertools

import tornado.web
import tornado.websocket


logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)


class WebSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        tornado.websocket.WebSocketHandler.__init__(
            self, application, request, **kwargs)
        self.url = None

    def initialize(self, url):
        self.url = url

    def open(self):
        logger.debug("websocket opened ")
        if (self.url == 'publish'):
            def sender():
                # just keep on looping
                counter = itertools.counter()
                for i in counter:
                    time.sleep(1)
                    msg = {
                        "now": datetime.datetime.now().isoformat(),
                        "i": i
                    }
                    self.write_message(json.dumps(msg))
            self.thread = threading.Thread(target=sender)
            self.thread.start()
    def on_message(self, message):
        # unicode, metadata message
        self.write_message(message)

    def on_close(self):
        logger.debug("websocket closed")


class HTTPHandler(tornado.web.RequestHandler):
    def initialize(self, size):
        # Message of 1MB
        message = '1' * 1000 * 1000
        self.message = size * message

    def get(self):
        self.set_header("Content-Type", "application/octet-stream")
        self.write(self.message)

def app():
    # register socket
    application = tornado.web.Application([
        (r"/echo", WebSocket, dict(url='echo')),
        (r"/publish", WebSocket, dict(url='publish')),
        # todo use an id scheme to attach to multiple models
        (r"/empty", HTTPHandler, dict(size=0)),
        (r"/100MB", HTTPHandler, dict(size=100))
    ])
    return application


def main():
    # Use common port not in services...
    # Normally you'd run this behind an nginx
    application = app()
    application.listen(22222)
    logger.info('serving at port 22222')
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
