# CSE 546 Cloud Computing Projects

This repository contains two cloud computing projects built around the same core task — face recognition on images/video frames — implemented using very different cloud architectures and elasticity models.

## [Project 1 — Elastic Face Recognition (IaaS)](./project_1)

A classic three-tier, Infrastructure-as-a-Service application deployed on raw EC2 instances:

- **Web tier**: a single always-on EC2 instance running a Flask server that accepts image uploads over HTTP, stores them in S3, and enqueues recognition requests via SQS.
- **App tier**: a fleet of EC2 instances (scaling from 0 to 15) that pull requests from SQS, run a FaceNet-based face recognition model (MTCNN + InceptionResnetV1), and write results back.
- **Custom autoscaling**: a hand-rolled controller monitors SQS queue depth and directly starts/stops app-tier EC2 instances (no AWS Auto Scaling group), following a one-request-per-instance policy.

Storage is handled via S3 (images and results) with SimpleDB used for optional result verification.

## [Project 2 — Serverless & Edge Face Recognition (PaaS)](./project_2)

Reimplements and extends the same face recognition pipeline using serverless and edge computing:

- **[Part 1](./project_2/part_1)**: Face detection and recognition run as two containerized AWS Lambda functions (packaged via ECR). A client posts an image to a Lambda Function URL, which triggers detection; a detected face is placed on an SQS queue that triggers a recognition Lambda, with the result returned via a response queue.
- **[Part 2](./project_2/part_2)**: Moves face **detection** to the edge. An emulated IoT device streams video frames over MQTT to an AWS IoT Greengrass core running locally, which performs face detection on-device and forwards only detected faces to the cloud for recognition — reducing cloud invocations and latency for frames with no face present.

## Key Differences

| | Project 1 | Project 2 |
|---|---|---|
| Compute model | IaaS — self-managed EC2 instances and a custom AMI | PaaS/serverless (Lambda) + edge computing (IoT Greengrass) |
| Elasticity | Custom autoscaling controller polling SQS to start/stop EC2 instances (0–15) | Automatic scaling built into Lambda concurrency — no custom autoscaler needed |
| Data flow | Images persisted to S3, referenced by key in SQS messages | Image data passed inline (base64) through Lambda payloads/MQTT messages |
| Where work happens | Entirely in the cloud (web tier + app tier) | Part 2 splits work between edge (detection) and cloud (recognition) |
| Packaging/deployment | Plain Python scripts on a custom EC2 AMI | Docker container images deployed via ECR to Lambda |
| Communication | HTTP + SQS | HTTP (Lambda Function URLs) + SQS, plus MQTT pub/sub and IoT device identity in Part 2 |

Both projects use the same underlying face detection/recognition model (`facenet-pytorch`: MTCNN for detection, InceptionResnetV1 for recognition), but Project 1 explores elasticity and autoscaling on raw infrastructure, while Project 2 explores serverless scaling and edge/cloud workload splitting.
