import logging
import atexit
import boto3

from flask import Flask, request
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

thread_executor = ThreadPoolExecutor(max_workers=2)

S3_BUCKET_NAME = "<ASU_ID>-in-bucket"
S3_client = boto3.client("s3", region_name="us-east-1")

SQS_REQUEST_QUEUE_NAME = "<ASU_ID>-req-queue"
SQS_REQUEST_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-req-queue"
SQS_RESPONSE_QUEUE_NAME = "<ASU_ID>-resp-queue"
SQS_RESPONSE_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-resp-queue"
SQS_client = boto3.client("sqs", region_name="us-east-1")


# Uploading image file to S3
def s3_upload(img_file, img_file_name):
    try:
        S3_client.put_object(
            Body=img_file,
            Bucket=S3_BUCKET_NAME,
            Key=img_file_name,
        )
        app.logger.info(f"Uploaded \"{img_file_name}\" to the bucket \"{S3_BUCKET_NAME}\".")
        return True
    except Exception as e:
        app.logger.error(f"{e}")
        app.logger.info(f"Failed to upload \"{img_file_name}\" to the bucket \"{S3_BUCKET_NAME}\".")
        return False

# Sending request to the Request queue
def send_request(img_file_name):
    response = None
    try:
        response = SQS_client.send_message(
            QueueUrl=SQS_REQUEST_QUEUE_URL,
            MessageBody=img_file_name
        )
        app.logger.info(f"Sent \"{img_file_name}\" to the \"{SQS_REQUEST_QUEUE_NAME}\" queue.")
    except Exception as e:
        app.logger.error(f"{e}")
        app.logger.info(f"Failed to pass \"{img_file_name}\" to \"{SQS_REQUEST_QUEUE_NAME}\" queue.")

    return response

# Checking the number of messages currenty in the Response queue
def get_available_responses_number():
    try:
        sqs_responses_response = SQS_client.get_queue_attributes(
            QueueUrl=SQS_RESPONSE_QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        return int(sqs_responses_response['Attributes']['ApproximateNumberOfMessages'])
    except:
        return(0)

# Receiving and checking responses from the Request queue
def receive_response(img_file_name):    
    while True:
        n_responses = get_available_responses_number()
        if n_responses == 0:
            continue

        try:
            recieve_message_response = SQS_client.receive_message(
                QueueUrl=SQS_RESPONSE_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=5,
                VisibilityTimeout=8
            )

            results = recieve_message_response.get('Messages', [])

            if results:
                app.logger.info(f"Searching for '{img_file_name}' in received messages.")
                for result in results:
                    if img_file_name not in result['Body']:
                        SQS_client.change_message_visibility(
                            QueueUrl=SQS_RESPONSE_QUEUE_URL,
                            ReceiptHandle=result['ReceiptHandle'],
                            VisibilityTimeout=0
                        )
                    else:
                        app.logger.info(f"Received result '{result['Body']}' from '{SQS_RESPONSE_QUEUE_URL}' queue.")
                        
                        delete_status = 0
                        while(delete_status != 200):
                            delete_msg_response = SQS_client.delete_message(
                                QueueUrl=SQS_RESPONSE_QUEUE_URL,
                                ReceiptHandle=result['ReceiptHandle']
                            )
                            delete_status = delete_msg_response['ResponseMetadata']['HTTPStatusCode']
                        
                        app.logger.info(f"Deleted result message for '{result['Body']}', Status Code: {delete_msg_response['ResponseMetadata']['HTTPStatusCode']}")
                        return result['Body']                         
            
            # app.logger.info(f"Failed to receive message from \"{SQS_RESPONSE_QUEUE_URL}\" queue.")
        except Exception as e:
            app.logger.error(f"{e}")
            app.logger.info(f"Failed to receive message from \"{SQS_RESPONSE_QUEUE_URL}\" queue.")


@app.route('/', methods=["POST"])
def detect_face():
    if request.method == "POST":
        img_file = request.files["inputFile"]
        img_file_name = img_file.filename

        S3_upload_status = s3_upload(img_file, img_file_name)
        send_request_status = send_request(img_file_name)
        
        img_file_name = img_file_name.split('.')[0]
        final_result = receive_response(img_file_name)
        app.logger.info(f"Final Result: {final_result}")

    return final_result, 200


def cleanup():
    app.logger.info("Executed cleanup!")
    thread_executor.shutdown(wait=True)

atexit.register(cleanup)