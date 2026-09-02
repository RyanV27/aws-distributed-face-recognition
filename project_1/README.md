# Elastic Face Recognition on AWS (IaaS)

A multi-tier cloud application that accepts an image over HTTP, runs it through a
face-recognition model, and returns the predicted name — with a custom, hand-rolled
autoscaling controller for the compute tier (no AWS Auto Scaling). Built for a cloud
computing course project (CSE546) using raw AWS IaaS primitives: EC2, S3, SQS, and
SimpleDB.

## Architecture

```
Client --POST /--> [Web Tier: server.py] --upload image--> S3 (input bucket)
                          |
                          '--enqueue filename--> SQS (request queue)
                                                        |
                                                        v
                                       [App Tier: backend.py] (0-15 EC2 instances)
                                                        |
                                          fetch image from S3, run face-match model
                                                        |
                                    write result --> S3 (output bucket)
                                    enqueue result --> SQS (response queue)
                          |
                          '--poll response queue, match filename, return to caller

[Autoscaling: controller.py] watches the request queue depth and starts/stops
app-tier EC2 instances (own algorithm, not AWS Auto Scaling).
```

- **Web tier** (`web-tier/`) — single always-on EC2 instance. Flask app (`server.py`)
  receives image uploads, stores them in S3, pushes a request to SQS, and blocks
  until the matching result appears on the response queue. `controller.py` is a
  separate long-running process that implements the autoscaling policy for the
  app tier.
- **App tier** (`app-tier/`) — `backend.py` runs on EC2 instances built from a
  custom AMI. Each instance pulls one request at a time from SQS, downloads the
  image from S3, runs face recognition, writes the result to S3, and pushes the
  result to the response queue. An instance stops itself once its queue is empty.
- **Face recognition model** (`face_recognition_model/`) — wraps a
  `facenet-pytorch` (MTCNN + InceptionResnetV1) pipeline and a precomputed
  embedding database (`data.pt`) used to match a detected face to a known name.
- **SimpleDB scripts** (`simpledb/`) — helper scripts used during development to
  verify that classification results were written correctly to SimpleDB.

## Repository layout

```
web-tier/               Flask web tier + autoscaling controller
app-tier/                Face-recognition worker that runs on app-tier EC2 instances
face_recognition_model/  Model code + embedding database used by the app tier
simpledb/                One-off scripts for inspecting/clearing a SimpleDB domain
docs/                    Misc. reference commands used during development
```

## Setup

This project targets `us-east-1` and expects the following AWS resources to
already exist, using your own identifier in place of `<ASU_ID>`:

| Resource | Name |
|---|---|
| S3 input bucket | `<ASU_ID>-in-bucket` |
| S3 output bucket | `<ASU_ID>-out-bucket` |
| SQS request queue | `<ASU_ID>-req-queue` (max message size 1 KB) |
| SQS response queue | `<ASU_ID>-resp-queue` |
| SimpleDB domain (optional) | `<ASU_ID>-simpleDB` |

Before running anything, search each script under `web-tier/` and `app-tier/`
for `<ASU_ID>` / `<AWS_ACCOUNT_ID>` placeholders and replace them with your own
bucket names, queue URLs, and AWS account ID. None of the scripts contain AWS
credentials — they all rely on the default boto3 credential chain, so configure
credentials via `aws configure`, environment variables, or (in production) an
EC2 instance IAM role.

1. **Web tier instance**: run `web-tier/setup.sh` to create a virtualenv and
   install Flask/gunicorn/boto3, then start `server.py` (see `docs/commands_to_run.txt`
   for gunicorn invocations) and `controller.py` alongside it.
2. **App tier AMI**: launch a base EC2 instance, run `app-tier/setup.sh` to
   install PyTorch/boto3, copy `app-tier/` and `face_recognition_model/` onto it,
   then create an AMI from that instance. Use the AMI to launch instances named
   `app-tier-instance-<n>`, initially left in the `stopped` state — the
   controller starts/stops them as load changes.
3. See `face_recognition_model/README.md` for a note on the model weights.

Full assignment requirements (naming conventions, autoscaling policy, grading)
are described in the course project spec and are summarized above; see each
subfolder's README for tier-specific details.
