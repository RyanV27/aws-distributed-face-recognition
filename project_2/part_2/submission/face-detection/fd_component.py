import queue
import base64
import boto3
import json
import os
import sys
import time
import traceback
import numpy as np
from io import BytesIO
from PIL import Image

from awsiot.greengrasscoreipc.clientv2 import GreengrassCoreIPCClientV2
from awsiot.greengrasscoreipc.model import (
    SubscriptionResponseMessage,
    UnauthorizedError
)

from fd_utils import FaceDetection

# Loading Boto3 client
SQS_REQUEST_QUEUE_NAME = "<ASU_ID>-req-queue"
SQS_REQUEST_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-req-queue"
SQS_RESPONSE_QUEUE_NAME = "<ASU_ID>-resp-queue"
SQS_RESPONSE_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-resp-queue"
SQS_client = boto3.client("sqs", region_name="us-east-1")

# Model for face detection
face_detector = FaceDetection()
buffer_io = BytesIO()


def on_stream_event(event: SubscriptionResponseMessage):
    try:
        message = str(event.binary_message.message, 'utf-8')
        topic = event.binary_message.context.topic
        # print(f'Received new message on topic {topic}')

        msg_data = json.loads(message)
        # print("Loaded JSON data from message.")

        encoded_img = msg_data.get("encoded")
        req_id = msg_data.get("request_id")
        file_path = msg_data.get("filename")

        image_bytes = base64.b64decode(encoded_img)
        input_image = Image.open(BytesIO(image_bytes))
        # print(f"Decoded the base64 image to pillow image.")
        
        # Using MTCNN to detect the face
        face_img = face_detector.face_detection_func(
            input_image=input_image,
            test_image_path=file_path
        )
        
        # Send image to Request queue if face is detected
        if face_img is None:
            # response = send_response_to_queue(req_id)
            message_body = {
                "request_id": req_id,
                "result": "No-Face"
            }
            message_body = json.dumps(message_body)

            # try:
            response = SQS_client.send_message(
                QueueUrl=SQS_RESPONSE_QUEUE_URL,
                MessageBody=message_body
            )
            print(f"Sent \"No-Face\" for \"{req_id}\" to the \"{SQS_RESPONSE_QUEUE_NAME}\" queue.")
        else:        
            # response = send_request_to_queue(req_id, face_img, file_path)
            buffer_io.seek(0)
            buffer_io.truncate(0)
            face_img.save(buffer_io, format="JPEG", quality=100)
            # file_img_bytes = buffer_io.getvalue()
            file_img_b64 = base64.b64encode(buffer_io.getvalue()).decode("utf-8")

            message_body = {
                "request_id": req_id,
                "face_image": file_img_b64
            }
            message_body = json.dumps(message_body)

            response = SQS_client.send_message(
                QueueUrl=SQS_REQUEST_QUEUE_URL,
                MessageBody=message_body
            )
            print(f"Sent \"{file_path}\" to the \"{SQS_REQUEST_QUEUE_NAME}\" queue.")
    except:
        traceback.print_exc()
    

def on_stream_error(error: Exception):
    print('Received an error from topic.', file=sys.stderr)
    traceback.print_exc()
    return False


def on_stream_closed():
    print('Topic stream subscribe has been closed.')


def main():
    topic = 'clients/<ASU_ID>-IoTThing'

    try:
        gg_ipc_client = GreengrassCoreIPCClientV2()
        _, operation = gg_ipc_client.subscribe_to_topic(
            topic=topic,
            on_stream_event=on_stream_event,
            on_stream_error=on_stream_error, 
            on_stream_closed=on_stream_closed
        )
        # print('Successfully subscribed to topic: ' + topic)

        try:
            while True:
                time.sleep(1)
        except InterruptedError:
            print('Subscribe to topic has been interrupted.')
    except (KeyboardInterrupt, SystemExit):
        print('KeyboardInterrupt or SystemExit encountered.')
        pass
    except UnauthorizedError:
        print('Unauthorized error while subscribing to topic: ', topic, file=sys.stderr)
        traceback.print_exc()
        exit(1)
    except Exception:
        print('Exception occurred', file=sys.stderr)
        traceback.print_exc()
        exit(1)
    finally:
        operation.close()


if __name__ == '__main__':
    main()
