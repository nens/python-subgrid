#!/usr/bin/env python
import logging
import threading
import time
import json
import datetime

import tornado.web
import tornado.websocket
import six

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

class WebSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        # self.zmqstream = kwargs.pop('zmqstream')
        tornado.websocket.WebSocketHandler.__init__(
            self, application, request, **kwargs)

    def initialize(self):
        pass

    def open(self):
        logger.debug("websocket opened ")
        def sender():
            for i in range(100):
                time.sleep(5)
                msg = {"now": datetime.datetime.now().isoformat()}
                self.write_message(json.dumps(msg))
        self.thread = threading.Thread(target=sender)
        self.thread.start()
    def on_message(self, message):
        # unicode, metadata message
        logger.debug("got message %20s, text: %s", message, isinstance(message, six.text_type))

    def on_close(self):
        logger.debug("websocket closed")


class HTTPHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def get(self):
        self.set_header("Content-Type", "application/json")
        self.write('ok')

def app():
    # register socket
    application = tornado.web.Application([
        (r"/", HTTPHandler),
        # todo use an id scheme to attach to multiple models
        (r"/ws", WebSocket),
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
