import json
import logging
import signal
import sys

from threading import Thread
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler

logger = logging.getLogger()

REGISTERED_GROUPS = {}

class AMPCrowdResponseServer(Thread, RequestHandler):
    def __init__(self, port, client):
        Thread.__init__(self)
        self.port = port
        urls = [('/response', ResponseHandler,
                 {
                     'client': client,
                 })]
        self.app = Application(urls)
        self.server = HTTPServer(self.app)
        self.daemon = True
        self.running = False
        self.client = client

        # handle interrupt
        self.old_sigint = signal.signal(signal.SIGINT, self.handle_interrupt)

    def run(self):
        logger.info("[WEB SERVER THREAD] starting response server...")
        self.server.listen(self.port)
        self.running = True
        IOLoop.instance().start()
        logger.info("[WEB SERVER THREAD] response server stopped.")
        self.running = False

    def stop(self):
        self.server.stop()
        ioloop = IOLoop.instance()
        ioloop.add_callback(lambda x: x.stop(), ioloop)
        logger.info("stopping response server...")

    def handle_interrupt(self, signal, frame):
        if self.running:
            logger.info("Caught interrupt.")
            self.stop()
        else:
            self.old_sigint(signal, frame)

    def register_group(self, group_id, point_id_set):
        if group_id in REGISTERED_GROUPS:
            raise ValueError("Group ID already in use: %s" % group_id)
        REGISTERED_GROUPS[group_id] = point_id_set

class ResponseHandler(RequestHandler):
    GROUP_MAP = {}

    def initialize(self, client):
        self.client = client

    def post(self):
        data = json.loads(self.get_body_argument('data'))
        logger.info("[WEB SERVER THREAD] received data.")
        logger.debug("[WEB SERVER THREAD] data: %s" % data)

        group_id = data['group_id']
        if group_id not in REGISTERED_GROUPS:
            raise ValueError("Response received for invalid group: %s" % group_id)
        if group_id not in self.GROUP_MAP:
            self.GROUP_MAP[group_id] = {}

        # Send data to point callback, and store it locally
        answers = data['answers']
        group_start_time = data['group_start_time']
        for answer in answers:
            self.GROUP_MAP[group_id][answer['identifier']] = answer
            logger.info("Calling user point callback.")
            try:
                self.client._handle_new_point(
                    group_id, group_start_time=group_start_time, **answer)
            except Exception:
                pass

        # Send data to the group callback if we're done.
        processed_point_ids = set(self.GROUP_MAP[group_id].keys())
        registered_point_ids = REGISTERED_GROUPS[group_id]
        if processed_point_ids == registered_point_ids:
            logger.info("Group has been processed.")
            logger.info("Calling user group callback.")
            try:
                self.client._handle_new_group(group_id)
            except Exception:
                pass

        # Debugging only, determine what keys are missing
        else:
            missing = registered_point_ids - processed_point_ids
            logger.debug("Still missing point ids: %s" % missing)

            unexpected = processed_point_ids - registered_point_ids
            logger.debug("Unexpected point ids: %s" % unexpected)
