import os
import json
import boto3
import base64
import numpy as np

from io import BytesIO
from PIL import Image
from facenet_pytorch import MTCNN

from utils import FaceDetection

# Model for face detection
face_detector = FaceDetection()

# Loading Boto3 client
SQS_REQUEST_QUEUE_NAME = "<ASU_ID>-req-queue"
SQS_REQUEST_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-req-queue"
SQS_client = boto3.client("sqs", region_name="us-east-1")

# Function to send request to the Request queue
def send_request(req_id, file_img, file_img_path):
    # Converting Pil image to base64 encoded text
    buffer_io = BytesIO()
    file_img.save(buffer_io, format="JPEG", quality=100)
    file_img_bytes = buffer_io.getvalue()
    file_img_b64 = base64.b64encode(file_img_bytes).decode("utf-8")

    message_body = {
        "request_id": req_id,
        "face_image": file_img_b64
    }
    message_body = json.dumps(message_body)

    response = None
    try:
        response = SQS_client.send_message(
            QueueUrl=SQS_REQUEST_QUEUE_URL,
            MessageBody=message_body
        )
        # print(f"Sent \"{os.path.basename(file_img_path)}\" to the \"{SQS_REQUEST_QUEUE_NAME}\" queue.")
    except Exception as e:
        print(f"{e}")
        print(f"Failed to pass \"{os.path.basename(file_img_path)}\" to \"{SQS_REQUEST_QUEUE_NAME}\" queue.")

    return response

def face_detection_handler(event, context):
    # Receiving the image from HTTP POST request
    try:
        if "body" in event:
            body_str = event["body"]
            if isinstance(body_str, str):
                event_body = json.loads(body_str)
            else:
                event_body = body_str
        else:
            # Event itself is the body (local testing)
            event_body = event
        
        # event_body = json.loads(event.get("body"))
        input_file = event_body["content"]
        req_id = event_body["request_id"]
        file_path = event_body["filename"]
        # print(f"Recieved event contents.")
    except Exception as e:
        print(e)
        print(f"Failed to read event data.")
        return {"statusCode": 400, "body": "Failed to read event data."}

    try:
        # Decoding the image from base64 to pillow image
        image_bytes = base64.b64decode(input_file)
        input_image = Image.open(BytesIO(image_bytes))
        # print(f"Converted image to base64 encoded string.")
    except Exception as e:
        print(e)
        print(f"Failed to convert image to base64 encoded string.")
        return {"statusCode": 400, "body": "Failed to convert image to base64 encoded string."}

    # Using MTCNN to detect the face
    try:
        face_img = face_detector.face_detection_func(
            input_image=input_image,
            test_image_path=file_path
        )
        # print("Performed face detection.")
    except Exception as e:
        print(e)
        print(f"Failed to convert image to base64 encoded string.")
        return {"statusCode": 400, "body": "Failed to convert image to base64 encoded string."}

    # Sending request to the Request queue
    try:
        response = send_request(req_id, face_img, file_path)
        # print("Sent detected face image to the queue.")
    except Exception as e:
        print(e)
        print(f"Failed to send detected face image to the queue.")
        return {"statusCode": 400, "body": "Failed to send detected face image to the queue."}

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "success"
        })
    }