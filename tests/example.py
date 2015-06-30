import logging
import uuid
from client import AMPCrowdClient

logger = logging.getLogger()

RESULTS = {}

def handle_result(group_id, identifier, value):
    logger.info("Example got new result for group %s" % group_id)
    logger.debug("Data: %s, %f" % (identifier, value))

def handle_group(group_id, answers):
    logger.info("Group %s completed" % group_id)
    logger.debug("Data: %s" % answers)
    logger.info("Stopping response server")
    client.stop_response_server()

if __name__ == '__main__':
    client = AMPCrowdClient('127.0.0.1', '8000', True)
    client.log_level(logging.DEBUG)
    pool_id = str(uuid.uuid4())
    data = {
        'group_id': str(uuid.uuid4()),
        'group_context': {},
        'content': {
            't1': 'This is t1',
            't2': 'This is t2',
            't3': 'This is t3'
        },
        'configuration': {
            'task_type': 'sa',
            'task_batch_size': 3,
            'num_assignments': 1,
            'callback_url': 'http://127.0.0.1:8001/response',
            'amt': {
                'sandbox' : True,
                'title': 'This is a retainer HIT!',
                'description': 'You will be on retainer',
                'reward': 0.04,
                'duration': 1000,
            },
            'retainer_pool': {
                'create_pool': True,
                'pool_id': pool_id,
                'pool_size': 1,
                'min_tasks_per_worker': 2,
                'waiting_rate': .02,
                'task_rate': .02,
                'list_rate': .04,
            },
        }
    }
    response_opts = {
        'host': '127.0.0.1',
        'port': '8001',
    }
    client.start_response_server(8001, handle_result, handle_group)
    client.create_task_group('amt', data)
    client.wait_for_responses()
    client.finish_retainer_pool('amt', {'pool_id': pool_id})
