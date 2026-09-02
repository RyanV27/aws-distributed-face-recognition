import boto3
import base64
import json
import numpy as np

from io import BytesIO
from PIL import Image
# from facenet_pytorch import InceptionResnetV1

from utils import FaceRecognition

# Model for face recognition
face_recognizer = FaceRecognition()
model_wt_path = './resnetV1_video_weights_1.pt'

# Loading Boto3 client
SQS_REQUEST_QUEUE_NAME = "<ASU_ID>-req-queue"
SQS_REQUEST_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-req-queue"
SQS_RESPONSE_QUEUE_NAME = "<ASU_ID>-resp-queue"
SQS_RESPONSE_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-resp-queue"
SQS_client = boto3.client("sqs", region_name="us-east-1")


def face_recognition_handler(event, context):
    batch_delete = []
    batch_response = []

    for record in event["Records"]:
        try:
            msg = json.loads(record["body"])
            print(msg["request_id"])
            decoded = base64.b64decode(msg["face_image"])
            buffer = BytesIO(decoded)
            face_arr = np.load(buffer, allow_pickle=True)

            result = face_recognizer.face_recognition_func(face_arr, model_wt_path)

            batch_delete.append({
                "Id": msg["request_id"],
                "ReceiptHandle": record["receiptHandle"]
            })

            batch_response.append({
                "Id": msg["request_id"],
                "MessageBody": json.dumps({
                    "request_id": msg["request_id"],
                    "result": result
                })
            })
        except Exception as e:
            print(e)
            continue

    if batch_response:
        SQS_client.send_message_batch(
            QueueUrl=SQS_RESPONSE_QUEUE_URL,
            Entries=batch_response
        )
    if batch_delete:
        SQS_client.delete_message_batch(
            QueueUrl=SQS_REQUEST_QUEUE_URL,
            Entries=batch_delete
        )

    return {"statusCode": 200}