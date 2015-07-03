import json
import logging

from conn import AMPCrowdConn
from response_server import AMPCrowdResponseServer

logger = logging.getLogger()

class AMPCrowdClient(object):

    def __init__(self, server_host, server_port=80, use_ssl=True):
        self.conn = AMPCrowdConn(server_host, server_port, use_ssl)
        self.response_server = None
        self.responses = {}
        self.new_point = False
        self.new_group = False

    def log_level(self, level=logging.INFO):
        logger.setLevel(level)

    def start_response_server(self, port):
        self.response_server = AMPCrowdResponseServer(port, self)
        self.response_server.start()

    def wait_for_responses(self, until=None): # until can be 'point' or 'group'
        self.new_point = False
        self.new_group = False
        until_str = ('a new %s is finished' % until
                     if until else 'the server is stopped')
        logging.info("Waiting for responses from AMPCrowd until %s..."
                     % until_str)
        stopped = False
        while True:
            self.response_server.join(1)
            if not self.response_server.is_alive():
                stopped = True
                break
            if until == 'point' and self.new_point:
                break
            elif until == 'group' and self.new_group:
                break
            logging.info("Still waiting for responses from AMPCrowd...")
        done_str = ('got a new %s' % until if until and not stopped
                    else 'server stopped')
        logging.info("%s. Done waiting for responses from AMPCrowd." % done_str)

    def _handle_new_group(self, group_id):
        self.new_group = True

    def _handle_new_point(self, group_id, identifier, **point_fields):
        if group_id not in self.responses:
            self.responses[group_id] = {}
        self.responses[group_id][identifier] = point_fields
        self.new_point = True

    def stop_response_server(self):
        self.response_server.stop()

    def create_task_group(self, crowd_name, config):
        # Register tasks with the response server
        if not self.response_server:
            raise ValueError("Can't run tasks without a response server!")
        self.response_server.register_group(config['group_id'],
                                            set(config['content'].keys()))

        # Make the request to AMPCrowd
        path = "/crowds/%s/tasks/" % crowd_name
        data = {'data': json.dumps(config)}
        logger.info("Creating new task group.")
        logger.debug("Request data: %s" % data)
        return self.conn.send_request(path, data)

    def finish_retainer_pool(self, crowd_name, config):
        path = "/crowds/%s/retainer/finish" % crowd_name
        if 'pool_id' not in config:
            raise ValueError("finish_retainer_pool requires a pool_id "
                             "parameter in the request data.")
        logger.info("Finishing retainer pool.")
        logger.debug("Request data: %s" % config)
        return self.conn.send_request(path, config)

    def purge_tasks(self, crowd_name):
        path = "/crowds/%s/purge_tasks/" % crowd_name
        logger.info("Purging tasks for crowd %s" % crowd_name)
        return self.conn.send_request(path)
