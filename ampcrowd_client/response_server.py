import json
import logging
import signal
import sys

from threading import Thread
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler

logger = logging.getLogger()

REGISTERED_GROUPS = {}

class AMPCrowdResponseServer(Thread, RequestHandler):
    def __init__(self, port, point_callback, group_callback):
        Thread.__init__(self)
        self.port = port
        urls = [('/response', ResponseHandler,
                 {
                     'point_callback': point_callback,
                     'group_callback': group_callback,
                 })]
        self.app = Application(urls)
        self.daemon = True

        # handle interrupt
        signal.signal(signal.SIGINT, self.handle_interrupt)

    def run(self):
        logger.info("[WEB SERVER THREAD] starting response server...")
        self.app.listen(self.port)
        IOLoop.instance().start()
        logger.info("[WEB SERVER THREAD] response server stopped.")

    def stop(self):
        ioloop = IOLoop.instance()
        ioloop.add_callback(lambda x: x.stop(), ioloop)
        logger.info("stopping response server...")

    def handle_interrupt(self, signal, frame):
        logger.info("Caught interrupt.")
        self.stop()

    def register_group(self, group_id, point_id_set):
        if group_id in REGISTERED_GROUPS:
            raise ValueError("Group ID already in use: %s" % group_id)
        REGISTERED_GROUPS[group_id] = point_id_set

class ResponseHandler(RequestHandler):
    GROUP_MAP = {}

    def initialize(self, point_callback, group_callback):
        self.point_callback = point_callback
        self.group_callback = group_callback

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
        for answer in answers:
            self.GROUP_MAP[group_id][answer['identifier']] = answer
            logger.info("Calling user point callback.")
            self.point_callback(group_id, **answer)

        # Send data to the group callback if we're done.
        processed_point_ids = set(self.GROUP_MAP[group_id].keys())
        registered_point_ids = REGISTERED_GROUPS[group_id]
        if processed_point_ids == registered_point_ids:
            logger.info("Group has been processed.")
            logger.info("Calling user group callback.")
            self.group_callback(group_id, self.GROUP_MAP[group_id].values())

        # Debugging only, determine what keys are missing
        else:
            missing = registered_point_ids - processed_point_ids
            logger.debug("Still missing point ids: %s" % missing)


            unexpected = processed_point_ids - registered_point_ids
            logger.debug("Unexpected point ids: %s" % unexpected)
