# Web Tier

Runs on a single, always-on EC2 instance (`web-instance`). Receives image
uploads over HTTP, hands them off to the app tier via S3 + SQS, and returns
the recognition result to the caller.

## Files

- **`server.py`** — Flask app. Handles `POST /` with the image under the
  `inputFile` form field:
  1. Uploads the image to the S3 input bucket, keyed by filename.
  2. Sends the filename as a message to the SQS request queue.
  3. Polls the SQS response queue for a message containing the filename,
     deletes it once found, and returns it as `<filename>:<prediction>` plain
     text. Non-matching messages are made visible again instead of consumed.
- **`controller.py`** — standalone autoscaling loop. Polls
  `ApproximateNumberOfMessages` on the request queue and starts stopped
  `app-tier-instance-*` EC2 instances (up to the number of pending requests,
  capped by however many are currently stopped) to bring the fleet size up to
  demand. Instances stop themselves in `backend.py` once idle. This — not AWS
  Auto Scaling — is the scaling mechanism for the app tier.
- **`gunicorn.conf.py`** — gunicorn config with `pre_request`/`post_request`
  hooks that track in-flight request count and a background thread that
  purges stale messages from the response queue once all workers have been
  idle for a while.
- **`setup.sh`** — creates a virtualenv (`cloud_venv`) and installs
  `boto3`, `flask`, `gunicorn`, `gevent`.

## Running

```bash
./setup.sh
source cloud_venv/bin/activate
gunicorn "server:app" -c gunicorn.conf.py &
python3 controller.py &
```

Before running, replace the `<ASU_ID>` / `<AWS_ACCOUNT_ID>` placeholders in
`server.py`, `controller.py`, and `gunicorn.conf.py` with your own bucket
names and queue URLs, and make sure AWS credentials are available (via
`aws configure`, environment variables, or an instance IAM role) with
permission to use S3, SQS, and EC2.

Assign the web tier instance an Elastic IP so its address stays stable.
