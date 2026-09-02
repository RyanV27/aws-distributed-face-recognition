import multiprocessing
import time
import threading

# Gunicorn settings
bind = "0.0.0.0:8000"
worker_class = "gevent"
workers = 10
worker_connections = 10

# Shared variables
n_working_requests = multiprocessing.Value('i', 0)
time_final_request = multiprocessing.Value('d', time.time())
is_purged_flag = multiprocessing.Value('b', True)

# Gunicorn Hooks
# For the worker to increment the counter by 1 before processing request
def pre_request(worker, req):
    with n_working_requests.get_lock():
        n_working_requests.value += 1

    with is_purged_flag.get_lock():
        is_purged_flag.value = False

# For the worker to decrement the counter by 1 after processing request
def post_request(worker, req, environ, resp):
    with n_working_requests.get_lock():
        n_working_requests.value -= 1

    with time_final_request.get_lock():
        time_final_request.value = time.time()

# Starts to execute right after server begins running
def when_ready(server):
    threading.Thread(target=monitor, args=(server,), daemon=True).start()

def monitor(server):
    # Added sleep timer to allow worker to import boto3 first and prevent half imports problem
    time.sleep(5)
    server.log.info(f"Monitor thread has begun running.")
    
    import boto3
    SQS_RESPONSE_QUEUE_NAME = "<ASU_ID>-resp-queue"
    SQS_RESPONSE_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-resp-queue"
    SQS_client = boto3.client("sqs", region_name="us-east-1")

    while True:
        with n_working_requests.get_lock():
            count_workers = n_working_requests.value
        with time_final_request.get_lock():
            idle_server_time = time.time() - time_final_request.value
        with is_purged_flag.get_lock():
            is_purged = is_purged_flag.value

        if count_workers == 0 and idle_server_time > 1 and is_purged == False:  
            server.log.info(f"All workers idle. Safe to purge '{SQS_RESPONSE_QUEUE_NAME}' queue.")

            # Checking for number of messages still in queue
            try:
                attribute_names = ['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible', 'ApproximateNumberOfMessagesDelayed']
                sqs_responses_response = SQS_client.get_queue_attributes(
                    QueueUrl=SQS_RESPONSE_QUEUE_URL,
                    AttributeNames=['All']
                )
                n_responses = sum(
                    int(sqs_responses_response['Attributes'][name])
                    for name in attribute_names
                )
            except:
                n_responses = 0

            if(n_responses <= 0):
                if(idle_server_time > 300):
                    with is_purged_flag.get_lock():
                        is_purged_flag.value = True
                time.sleep(1)
                continue

            server.log.info(f"Messages still present in '{SQS_RESPONSE_QUEUE_NAME}' queue. Purging messages!")
            try:
                SQS_client.purge_queue(QueueUrl=SQS_RESPONSE_QUEUE_URL)
            except SQS_client.exceptions.PurgeQueueInProgress:
                server.log.info("Purge already in progress. Must wait for 60 seconds before purging again.")

        time.sleep(2)