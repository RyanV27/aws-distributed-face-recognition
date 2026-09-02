import time
import boto3

SQS_REQUEST_QUEUE_NAME = "<ASU_ID>-req-queue"
SQS_REQUEST_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/<AWS_ACCOUNT_ID>/<ASU_ID>-req-queue"
SQS_client = boto3.client("sqs", region_name="us-east-1")

EC2_client = boto3.client("ec2", region_name="us-east-1")


# Checking the number of messages currenty in the Request queue
def get_available_requests_number():
    try:
        sqs_requests_response = SQS_client.get_queue_attributes(
            QueueUrl=SQS_REQUEST_QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        return int(sqs_requests_response['Attributes']['ApproximateNumberOfMessages'])
    except:
        return(0)


# Gettiing the number of currently stopped EC2 instances
def get_instances_number():
    filter = {'Name': 'tag:Name', 'Values': ['app-tier-instance-*']}

    # Retrieving stopped instances
    stopped_response = EC2_client.describe_instances(
        Filters=[filter, {'Name': 'instance-state-name', 'Values': ['stopped']}]
    )
    stopped_instances = [
        i['InstanceId']
        for r in stopped_response['Reservations']
        for i in r['Instances']
    ]

    return stopped_instances


def main():
    while True:
        n_available_requests = get_available_requests_number()
        instances_stopped = get_instances_number()
        n_instances_stopped = len(instances_stopped)

        print(f"\nRequests in queue: {n_available_requests}")
        print(f"Number of stopped instances: {n_instances_stopped}")
        print(f"Number of running instances: {15 - n_instances_stopped}")

        if (n_available_requests > 0) and (n_instances_stopped > 0):
            n_instances_to_start = min(n_available_requests, n_instances_stopped)
            try:
                EC2_client.start_instances(InstanceIds=instances_stopped[:n_instances_to_start])
                print(f"Started {n_instances_to_start} to handle requests.")
            except Exception as e:
                print(f"Error: {e}")
                print(f"Failed to start {n_instances_to_start} instances.")
                print(f"Instance IDs: {instances_stopped}")
        
        if n_available_requests == 0:
            time.sleep(1)


if __name__ == "__main__":
    main()