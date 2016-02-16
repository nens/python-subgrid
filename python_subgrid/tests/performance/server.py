#!/usr/bin/env python
import logging
import threading
import time
import json
import datetime
import itertools

import tornado.web
import tornado.websocket


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


class PubWebSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        tornado.websocket.WebSocketHandler.__init__(
            self, application, request, **kwargs)

    def initialize(self):
        pass

    def open(self, *args, **kwargs):
        logger.debug("websocket opened")
        def sender():
            # just keep on looping
            logger.info('starting to send')
            counter = itertools.count()
            for i in counter:
                time.sleep(1)
                msg = {
                    "now": datetime.datetime.utcnow().isoformat(),
                    "i": i
                }
                try:
                    self.write_message(json.dumps(msg))
                except:
                    logger.exception("stop sending")
                    break

        self.thread = threading.Thread(target=sender)
        self.thread.start()
    def on_close(self):
        logger.debug("websocket closed")


class Pub100WebSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        tornado.websocket.WebSocketHandler.__init__(
            self, application, request, **kwargs)


    def initialize(self):
        pass

    def open(self, *args, **kwargs):
        logger.debug("websocket opened")
        # message, fill in the rest later
        message = '1' * 1000 * 1000
        msg = {
            "now": '%s',
            "message": message
        }
        msg = json.dumps(msg)
        def sender():
            # just keep on looping
            logger.info('starting to send')
            counter = itertools.count()
            for i in counter:
                time.sleep(1)
                try:
                    self.write_message(
                        msg % (datetime.datetime.utcnow().isoformat(), )
                    )
                except:
                    logger.exception("stop sending")
                    break
        self.thread = threading.Thread(target=sender)
        self.thread.start()
    def on_close(self):
        logger.debug("websocket closed")

class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        tornado.websocket.WebSocketHandler.__init__(
            self, application, request, **kwargs)
    def initialize(self):
        pass

    def open(self, *args, **kwargs):
        logger.debug("websocket opened")

    def on_message(self, message):
        # unicode, metadata message
        self.write_message(message)

    def on_close(self):
        logger.debug("websocket closed")

class RequestReplyWebSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        tornado.websocket.WebSocketHandler.__init__(
            self, application, request, **kwargs)
    def initialize(self, size):
        self.size = size
        message = '1' * 1000 * 1000
        self.message = size * message

    def open(self, *args, **kwargs):
        logger.debug("websocket opened")

    def on_message(self, message):
        # unicode, metadata message
        self.write_message(self.message)

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

class MainHTTPHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "text/html")
        self.write('<h1>Ok</h1>')

def app():
    # register socket
    application = tornado.web.Application([
        (r"/", MainHTTPHandler),
        (r"/echo", EchoWebSocket),
        (r"/echo100", RequestReplyWebSocket, dict(size=1)),
        (r"/publish", PubWebSocket),
        (r"/pub100", Pub100WebSocket),
        # todo use an id scheme to attach to multiple models
        (r"/empty", HTTPHandler, dict(size=0)),
        # 1 MB for now
        (r"/100MB", HTTPHandler, dict(size=1))
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
