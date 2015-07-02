import logging
import uuid
from ampcrowd_client import AMPCrowdClient

logger = logging.getLogger()

RESULTS = {}

def handle_point(group_id, identifier, value):
    logger.info("Example got new result for group %s" % group_id)
    logger.debug("Data: %s, %f" % (identifier, value))

def handle_group(group_id, answers):
    logger.info("Group %s completed" % group_id)
    logger.debug("Data: %s" % answers)

if __name__ == '__main__':
    # Set up state for the API calls
    pool_id = str(uuid.uuid4())
    group_id = str(uuid.uuid4())
    data = {
        'group_id': group_id,
        'group_context': {},

        # 3 fake tweets for sentiment analysis
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

            # Settings for Amazon's Mechanical Turk
            'amt': {
                'sandbox' : True,
                'title': 'This is a retainer HIT!',
                'description': 'You will be on retainer',
                'reward': 0.04,
                'duration': 1000,
            },

            # Set up a retainer pool for real-time responses.
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

    # Initialize the AMPCrowd client
    client = AMPCrowdClient('127.0.0.1', '8000', True)
    client.log_level(logging.DEBUG)

    # Start the response server
    client.start_response_server(8001)

    # Create the tasks on AMPCrowd
    client.create_task_group('amt', data)

    # Wait until the first point is processed
    client.wait_for_responses(until='point')
    responses = client.responses[group_id]
    point_id = responses.keys()[0]
    handle_point(group_id, point_id, responses[point_id])

    # Wait for the group to finish
    client.wait_for_responses(until='group')
    responses = client.responses[group_id]
    handle_group(group_id, responses)

    # Tell AMPCrowd to shut down the retainer pool we created
    client.finish_retainer_pool('amt', {'pool_id': pool_id})

    # Stop the response server
    logger.info("Stopping response server")
    client.stop_response_server()
