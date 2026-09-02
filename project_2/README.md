# CSE546 Cloud Computing — Project 2: Serverless & Edge Face Recognition

This project builds a face detection + face recognition pipeline on AWS, first as
pure serverless Lambda functions (Part I), then extended to run face **detection**
at the edge via AWS IoT Greengrass while face **recognition** stays in the cloud
(Part II).

## Structure

- [`part_1/`](part_1/README.md) — Face detection & recognition as two AWS Lambda
  functions packaged in Docker container images, built on top of `facenet-pytorch`
  (MTCNN for detection, FaceNet/ResNet for recognition).
- [`part_2/`](part_2/README.md) — Edge computing extension: an emulated IoT device
  publishes video frames over MQTT to an AWS IoT Greengrass Core component that runs
  face detection locally, then forwards detected faces to SQS, which triggers the
  cloud-side face-recognition Lambda from Part I.

## What was intentionally left out of this repo

Both parts originally contained AWS credentials, private SSH keys (`.pem`), and
large binary/data files (trained model weights, sample face images, video, a
vendored copy of `facenet-pytorch`). None of that is included here:

- **Credentials & keys** — AWS access keys and `.pem` SSH keys were removed
  entirely (not redacted-in-place, just excluded) since they belonged to live
  AWS infrastructure. If you're re-running this, generate your own.
- **Model weights & large data** (`resnetV1.pt`, `resnetV1_video_weights_1.pt`,
  `aws-lambda-rie`, sample images/video, `fd.zip`) — these are either
  regenerable, downloadable, or `pip`-installable; see each part's README for
  how to obtain them.
- **Vendored `facenet_pytorch` library** — not copied; it's a normal PyPI
  dependency (`pip install facenet-pytorch`) declared in each `requirements.txt`.

See each part's README for exact setup steps.
