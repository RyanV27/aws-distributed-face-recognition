# Part 2 — Edge Computing with AWS IoT Greengrass

Extends Part 1 by moving face **detection** out of Lambda and onto an edge
device, using AWS IoT Greengrass. Face **recognition** stays in the cloud as a
Lambda function, now triggered via SQS instead of being called directly.

## Architecture

1. **Emulated IoT device** (EC2, Ubuntu) — publishes video frames as
   base64-encoded JSON MQTT messages to AWS IoT Core (`test_fd.py` acts as this
   publisher/workload generator).
2. **Greengrass Core device** (EC2, Amazon Linux 2023) — runs the
   `com.clientdevices.FaceDetection` Greengrass component (recipe:
   `com.clientdevices.FaceDetection-1.0.0.json`), which subscribes to the MQTT
   topic, runs MTCNN face detection locally (`fd_component.py` + `fd_utils.py`),
   and on a detected face, sends the cropped face image to an SQS **request**
   queue.
3. **Cloud Lambda** — `face-recognition` Lambda (`fr_lambda.py` + `fr_utils.py`,
   same model as Part 1) is triggered by the SQS request queue, computes the
   face embedding, matches it against precomputed embeddings, and writes the
   result to an SQS **response** queue.

## Layout

```
com.clientdevices.FaceDetection-1.0.0.json   # Greengrass component recipe
fd_utils.py                                   # FaceDetection (MTCNN wrapper), used by the Greengrass component
fr_utils.py                                   # FaceRecognition (embedding + nearest-match), used by the Lambda
test_fd.py                                    # MQTT publisher: sends test images/video frames to IoT Core

files_for_docker_image/                       # Docker image for the cloud-side face-recognition Lambda
  Dockerfile
  fd_lambda.py, fr_lambda.py, utils.py
  requirements.txt
  test/test_fd.py, test_fr.py
  numpy_batch_sqs/                            # variant that batches SQS messages via numpy instead of one-by-one
    fr_lambda_numpy_batch_sqs.py
    numpy_test_fr.py
    numpy_utils.py

from_ec2/                                     # development history of the Greengrass component, pulled from the
                                               # Greengrass Core EC2 instance (kept for reference/progression)
  fd_component.py                             # final/current version
  fd_component_0.py, _1.py, _2.py             # earlier iterations
  fd_component_client_threads.py
  fd_component_worker_threads.py
  fd_component_pre_final.py
  com.clientdevices.FaceDetection-1.0.0.json

submission/                                   # final graded submission bundle (credentials/ subfolder removed)
  face-detection/fd_component.py
  face-recognition/fr_lambda.py
```

## Not included (excluded on purpose)

- **Credentials & keys** — `web_instance_key.pem`,
  `files_for_docker_image/<ASU_ID>.pem`, and the entire
  `submission/credentials/` folder (which contained an AWS access key/secret,
  an EC2 elastic IP, and an SQS queue URL) are **not** in this repo. These
  were real, live AWS grading credentials issued for the assignment — if
  you're reusing this code, generate your own IAM user/keys and EC2 key pair.
- **Model weights** (`resnetV1.pt`, `resnetV1_video_weights_1.pt`) and
  **`aws-lambda-rie`** — see Part 1's README; same story here, they live under
  `files_for_docker_image/`.
- **`fd.zip`** — a ~22 MB archive bundling code/assets already present in this
  directory; not needed once the individual files are here.
- **Vendored `facenet_pytorch/`** — the original project vendored a full copy
  of the `facenet-pytorch` GitHub repo (including its sample images, model
  weights, and demo videos). This repo instead depends on it as a normal
  package: `pip install facenet-pytorch` (already in
  `files_for_docker_image/requirements.txt`).

## Setup

1. **Cloud side (face-recognition Lambda)** — same as Part 1: build the
   Docker image in `files_for_docker_image/` (after adding the model weight
   files and `aws-lambda-rie` if testing locally), push to ECR, deploy as a
   Lambda function, and configure it as a target of your SQS request queue.
2. **Greengrass Core device** — provision an EC2 instance, install AWS IoT
   Greengrass Nucleus, create an IoT "thing", and deploy the
   `com.clientdevices.FaceDetection` component using the recipe in
   `com.clientdevices.FaceDetection-1.0.0.json` (this installs
   `awsiotsdk`, `boto3`, `torch`, `torchvision`, `torchaudio` and runs
   `fd_component.py`, which uses `fd_utils.py`).
3. **Emulated IoT device** — on a separate EC2 instance, run `test_fd.py` to
   publish frames over MQTT to AWS IoT Core, which routes them to the
   Greengrass Core device.
4. Configure your own AWS IoT certificates, IAM roles/policies, and SQS queue
   URLs/names in place of the placeholders in the code (queue names/URLs in
   `fd_lambda.py`/`fr_lambda.py` reference the original assignment's specific
   AWS account and queues).
