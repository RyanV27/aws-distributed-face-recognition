import boto3
import io
import requests
from PIL import Image

from face_recognition_model.facenet_pytorch import MTCNN, InceptionResnetV1
from face_recognition_model import face_match

SQS_REQUEST_QUEUE_NAME = "<ASU_ID>-req-queue"
SQS_REQUEST_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-req-queue"
SQS_RESPONSE_QUEUE_NAME = "<ASU_ID>-resp-queue"
SQS_RESPONSE_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-resp-queue"
SQS_client = boto3.client("sqs", region_name="us-east-1")

S3_INPUT_BUCKET_NAME = "<ASU_ID>-in-bucket"
S3_OUTPUT_BUCKET_NAME = "<ASU_ID>-out-bucket"
S3_client = boto3.client("s3", region_name="us-east-1")

# Getting the EC2 instance id for stopping the instance
EC2_client = boto3.client("ec2", region_name="us-east-1")
try:
    session_token = requests.put(
        "http://169.254.169.254/latest/api/token",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
        timeout=2
    ).text
    
    EC2_INSTANCE_ID = requests.get(
        "http://169.254.169.254/latest/meta-data/instance-id",
        headers={"X-aws-ec2-metadata-token": session_token},
        timeout=2
    ).text
except Exception:
    pass

def get_available_requests_number():
    try:
        sqs_requests_response = SQS_client.get_queue_attributes(
            QueueUrl=SQS_REQUEST_QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        return int(sqs_requests_response['Attributes']['ApproximateNumberOfMessages'])
    except:
        return(0)

def main():
    idle_wait = 0
    while True:
        n_requests = get_available_requests_number()
        print(f"Number of requests: {n_requests}")
        if n_requests == 0:
            if idle_wait >= 3:
                break
            else:
                idle_wait += 1
                continue

        idle_wait = 0
        # Receiving request from request queue
        try:
            messages = SQS_client.receive_message(
                QueueUrl=SQS_REQUEST_QUEUE_URL,
                MaxNumberOfMessages=1,
                VisibilityTimeout=1,
                WaitTimeSeconds=2
            )
        except Exception as e:
            print(f"Failed to receive message from \"{SQS_REQUEST_QUEUE_NAME}\" queue.")

        if 'Messages' in messages:
            print("Message found in queue:")
            print(messages['Messages'][0]['Body'])
            img_file_name = messages['Messages'][0]['Body']
        else:
            print("No messages found (might not have arrived yet or was already processed).")
            continue

        # Fetching image from the S3 input bucket.
        try:  
            s3_input_response = S3_client.get_object(
                Bucket=S3_INPUT_BUCKET_NAME, 
                Key=img_file_name
            )
            img_data = s3_input_response['Body'].read()
            print(f"Received image '{img_file_name}' from '{S3_INPUT_BUCKET_NAME}' bucket.")
        except Exception as e:
            print(f"Failed to get image '{img_file_name}' from '{S3_INPUT_BUCKET_NAME}' bucket.")
            continue

        img = Image.open(io.BytesIO(img_data))

        # Performing face recognition with the model. 
        mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20) 
        resnet = InceptionResnetV1(pretrained='vggface2').eval()
        face_match_result = face_match(img, "./face_recognition_model/data.pt", mtcnn, resnet)

        # Deleting the request from request queue
        try: 
            SQS_client.delete_message(
                QueueUrl=SQS_REQUEST_QUEUE_URL,
                ReceiptHandle=messages['Messages'][0]['ReceiptHandle']
            )
            print(f"Deleted request for '{img_file_name}' from '{SQS_REQUEST_QUEUE_NAME}' queue.")
        except Exception as e:
            print(f"Failed to delete request from '{SQS_REQUEST_QUEUE_NAME}' queue.")
            continue

        # Storing recognition result in the S3 output bucket.  
        img_file_name = img_file_name.split('.')[0]
           
        try:
            S3_client.put_object(
                Body=face_match_result[0],
                Bucket=S3_OUTPUT_BUCKET_NAME,
                Key=img_file_name,
            )
            print(f"Uploaded \"{img_file_name}\" to the bucket \"{S3_OUTPUT_BUCKET_NAME}\".")
        except Exception as e:
            print(f"Error: {e}")
            print(f"Failed to upload \"{img_file_name}\" to the bucket \"{S3_OUTPUT_BUCKET_NAME}\".")
            continue

        # Pushing recognition result to the response queue. 
        result = img_file_name + ":" + face_match_result[0]
        try:
            SQS_client.send_message(
                QueueUrl=SQS_RESPONSE_QUEUE_URL,
                MessageBody=result
            )
            print(f"Sent the result '{result}' to \"{SQS_RESPONSE_QUEUE_NAME}\" queue.")
        except Exception as e:
            print(f"Error: {e}")
            print(f"Failed to pass the result '{result}' to \"{SQS_RESPONSE_QUEUE_NAME}\" queue.")
            continue

    # Stopping the EC2 instance when no request received
    if EC2_INSTANCE_ID:
        EC2_client.stop_instances(InstanceIds=[EC2_INSTANCE_ID])
        

if __name__ == "__main__":
    main()