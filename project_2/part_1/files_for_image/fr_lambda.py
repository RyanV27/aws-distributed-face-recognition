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


def delete_req_message(request_id, receipt_handle):
    try: 
        SQS_client.delete_message(
            QueueUrl=SQS_REQUEST_QUEUE_URL,
            ReceiptHandle=receipt_handle
        )
        print(f"Deleted request '{request_id}' from '{SQS_REQUEST_QUEUE_NAME}' queue.")
    except Exception as e:
        print(f"Failed to delete request '{request_id}' from '{SQS_REQUEST_QUEUE_NAME}' queue.")


def send_response(response_dict):
    try:
        SQS_client.send_message(
            QueueUrl=SQS_RESPONSE_QUEUE_URL,
            MessageBody=json.dumps(response_dict)
        )
        print(f"Sent the result '{response_dict['request_id']}'->'{response_dict['result']}' to \"{SQS_RESPONSE_QUEUE_NAME}\" queue.")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Failed to pass the result '{response_dict['request_id']}'->'{response_dict['result']}' to \"{SQS_RESPONSE_QUEUE_NAME}\" queue.")


def face_recognition_handler(event, context):
    for record in event["Records"]:
        # Decoding the image from base64 to pillow image
        try:
            message_body_dict = json.loads(record["body"])
            # print("Received message from response queue.")
        except Exception as e:
            print(e)
            print(f"Failed to receive message from response queue.")
            continue

        # Converting base64 string to pillow image
        try:
            face_img_bytes = base64.b64decode(message_body_dict["face_image"])
            face_img = Image.open(BytesIO(face_img_bytes))
            # print("Decoded base64 string to pillow images.")
        except Exception as e:
            print(e)
            print(f"Failed to decode base64 string to pillow images.")
            continue
    
        # Getting the name of the face using ResNet
        try:
            face_result = face_recognizer.face_recognition_func(face_img, model_wt_path)  
            # print("Performed face recognition.")
        except Exception as e:
            print(e)
            print(f"Failed to perform face recognition.")
            continue

        # Deleting request from Request queue after processing
        try:
            delete_req_message(message_body_dict['request_id'], record['receiptHandle']) 
            # print("Deleted message from the queue.")     
        except Exception as e:
            print(e)
            print(f"Failed to delete message from the queue.")

        response_dict = {
            "request_id": message_body_dict['request_id'],
            "result": face_result
        }

        # Sending the result to Response Queue 
        try:
            send_response(response_dict)
            # print("Sent response to the response queue.")
        except Exception as e:
            print(e)
            print(f"Failed to send response to the response queue.")
            continue

    return {"statusCode": 200}