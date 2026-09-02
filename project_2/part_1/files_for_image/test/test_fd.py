import base64
import json
import uuid
import requests
from fd_lambda import face_detection_handler

image_path = '/home/ryan/cse546_cloud_computing/CSE546-FALL-2025/video_frames_100/test_02.jpg'
lambda_url = "http://localhost:9000/2015-03-31/functions/function/invocations"  
# lambda_url = 'https://irc5xpvgexnwnfe2s2h4hxjkhe0xajbg.lambda-url.us-east-1.on.aws/'

with open(image_path, "rb") as f:
  encoded_file = base64.b64encode(f.read()).decode("utf-8")

request_id  = str(uuid.uuid4())
payload     = json.dumps({"request_id": request_id, "content": encoded_file, "filename": image_path})
headers     = {"Content-Type": "application/json"}

with open("fd_request.json", "w") as f:
    json.dump({"request_id": request_id, "content": encoded_file, "filename": image_path}, f)

try:
  # response = requests.post(lambda_url, data=payload, headers=headers)
  print("Response:\n", response.json())
except Exception as e:
  print(e)
  print("Failed request to face detector.")

# # Simulated API Gateway HTTP POST event
# event = {
#   "version": "2.0",
#   "routeKey": "$default",
#   "rawPath": "/",
#   "rawQueryString": "",
#   "headers": {
#     "content-type": "application/json"
#   },
#   "requestContext": {
#     "http": {
#       "method": "POST",
#       "path": "/"
#     }
#   },
#   "body": json.dumps({"request_id": request_id, "content": encoded_file, "filename": image_path}),
#   "isBase64Encoded": True
# }

# response = face_detection_handler(event, None)

# print(response)