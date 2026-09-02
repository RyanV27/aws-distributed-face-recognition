import boto3
import base64
import json

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
    for record in event["Records"]:

        message_body_dict = json.loads(record["body"])

        face_img_bytes = base64.b64decode(message_body_dict["face_image"])
        face_img = Image.open(BytesIO(face_img_bytes))

        face_result = face_recognizer.face_recognition_func(face_img, model_wt_path)

        SQS_client.delete_message(
            QueueUrl=SQS_REQUEST_QUEUE_URL,
            ReceiptHandle=record["receiptHandle"]
        )
        print(f"Deleted request '{message_body_dict['request_id']}' from '{SQS_REQUEST_QUEUE_NAME}' queue.")

        response_dict = {
            "request_id": message_body_dict["request_id"],
            "result": face_result
        }

        SQS_client.send_message(
            QueueUrl=SQS_RESPONSE_QUEUE_URL,
            MessageBody=json.dumps(response_dict)
        )
        print(f"Sent the result '{response_dict['request_id']}' -> '{response_dict['result']}' to \"{SQS_RESPONSE_QUEUE_NAME}\" queue.")

    return {"statusCode": 200}