import json
import numpy as np
from io import BytesIO
from PIL import Image
import base64

from fr_lambda import face_recognition_handler

def encode_image_to_b64(path):
    img = Image.open(path)
    arr = np.array(img)
    buffer = BytesIO()
    np.save(buffer, arr, allow_pickle=True)
    arr_bytes = buffer.getvalue()
    return base64.b64encode(arr_bytes).decode("utf8")

def main():
    image_paths = [
        "/home/ryan/cse546_cloud_computing/CSE546-FALL-2025/video_frames_100/test_02.jpg",
        "/home/ryan/cse546_cloud_computing/CSE546-FALL-2025/video_frames_100/test_03.jpg",
        "/home/ryan/cse546_cloud_computing/CSE546-FALL-2025/video_frames_100/test_04.jpg"
    ]

    records = []
    for index, path in enumerate(image_paths):
        img_b64 = encode_image_to_b64(path)
        record = {
            "body": json.dumps({
                "request_id": str(index + 1),
                "face_image": img_b64
            }),
            "receiptHandle": "RH" + str(index + 1)
        }
        records.append(record)

    event = {"Records": records}

    print("Sent images.")
    response = face_recognition_handler(event, None)
    print("Handler response:", response)

if __name__ == "__main__":
    main()