import json
from io import BytesIO
from PIL import Image
import base64

from fr_lambda import face_recognition_handler

def main():
    img_path = '/home/ryan/cse546_cloud_computing/CSE546-FALL-2025/video_frames_100/test_02.jpg'

    # img = Image.new("RGB", (100, 100), color="blue")
    img = Image.open(img_path)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=100)
    img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Create fake SQS event payload
    event = {
        "Records": [
            {
                "body": json.dumps({"request_id": "1", "face_image": img_b64}),
                "receiptHandle": "QWE123"
            }
        ]
    }

    # Call handler directly
    response = face_recognition_handler(event, None)
    print("Handler response:", response)

if __name__ == "__main__":
    main()