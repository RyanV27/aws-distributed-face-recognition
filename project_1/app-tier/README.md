# App Tier

Runs on EC2 instances (`app-tier-instance-<n>`) built from a custom AMI, scaled
between 0 and 15 by the web tier's `controller.py`. Each instance processes
exactly one request at a time and stops itself once no work is left.

## Files

- **`backend.py`** — worker loop:
  1. Polls the SQS request queue for a message (an image filename).
  2. Downloads the corresponding image from the S3 input bucket.
  3. Runs face recognition via `face_recognition_model.face_match`.
  4. Deletes the request from the request queue.
  5. Writes the predicted name to the S3 output bucket, keyed by filename
     (without extension).
  6. Sends `<filename>:<prediction>` to the SQS response queue.
  Exits (and stops its own EC2 instance via the instance metadata service)
  after a few consecutive empty polls.
- **`setup.sh`** — creates a virtualenv (`cloud_venv`) and installs the CPU
  build of PyTorch plus `boto3`/`requests`.

## Building the AMI

1. Launch a base EC2 instance (Amazon Linux or Ubuntu).
2. Run `setup.sh` on it to install dependencies.
3. Copy `backend.py` and the `face_recognition_model/` directory onto the
   instance (see `docs/commands_to_run.txt` for example `scp` commands).
4. Create an AMI from this instance.
5. Launch your app-tier instances from that AMI, named
   `app-tier-instance-<n>`, and leave them in the `stopped` state — the web
   tier's controller starts them as demand requires.

Before running, replace the `<ASU_ID>` / `<AWS_ACCOUNT_ID>` placeholders in
`backend.py` with your own bucket names and queue URLs, and ensure the
instance has an IAM role (or configured credentials) with access to S3, SQS,
and `ec2:StopInstances` on itself.
