import os
import sys
import json
import uuid
import time
import base64
import random
import pandas as pd
from PIL import Image
import io as cse_io
from awsiotsdk import mqtt_connection_builder
from awsiotsdk.mqtt import QoS
import threading

stop_event = threading.Event()

class CmdData:
    def __init__(self, topic, max_ops):
        self.input_topic = topic
        self.input_max_pub_ops = max_ops

def load_image_paths(folder):
    items = []
    for entry in os.listdir(folder):
        full = os.path.join(folder, entry)
        if os.path.isfile(full):
            items.append(full)
    return items

def publish_requests(image_path_list, mqtt_connection, cmdData, prediction_df):
    random.seed(42)
    random.shuffle(image_path_list)

    publish_data = {}
    loop_count = 0
    max_ops = cmdData.input_max_pub_ops

    while loop_count < max_ops:
        request_id = str(uuid.uuid4())
        image_path = image_path_list[loop_count]
        filename = os.path.basename(image_path)

        with Image.open(image_path) as img:
            img = img.resize((512, 512))
            buffer = cse_io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)
            encoded_file = base64.b64encode(buffer.read()).decode("utf8")

        message = {
            "request_id": request_id,
            "sequence": loop_count,
            "filename": filename,
            "encoded": encoded_file
        }

        payload = json.dumps(message)
        pub_future, _ = mqtt_connection.publish(
            cmdData.input_topic,
            payload,
            QoS.AT_MOST_ONCE
        )

        if prediction_df is not None:
            try:
                ground_truth = prediction_df.loc[
                    prediction_df["Image"] == filename,
                    "Results"
                ].values[0]
            except:
                ground_truth = None
        else:
            ground_truth = None

        publish_data[request_id] = {
            "ground_truth": ground_truth,
            "pub_time": time.time()
        }

        time.sleep(2)
        loop_count += 1

    print("Publishing complete")
    stop_event.set()

def main():
    if len(sys.argv) < 5:
        print("Usage:")
        print("python3 test_face_detection_publish.py <image_folder> <asu_id> <topic> <max_messages> [ground_truth_csv]")
        return

    folder = sys.argv[1]
    asu = sys.argv[2]
    topic = sys.argv[3]
    max_messages = int(sys.argv[4])

    if len(sys.argv) == 6:
        csv_path = sys.argv[5]
        prediction_df = pd.read_csv(csv_path)
    else:
        prediction_df = None

    images = load_image_paths(folder)
    if len(images) == 0:
        print("No images found in folder")
        return

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint="localhost",
        port=8883,
        cert_filepath=None,
        pri_key_filepath=None,
        ca_filepath=None,
        client_id=f"tester{asu}",
        clean_session=True,
        keep_alive_secs=30
    )

    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("Connected to Greengrass MQTT")

    cmdData = CmdData(topic, max_messages)

    publish_requests(images, mqtt_connection, cmdData, prediction_df)

    mqtt_connection.disconnect()
    print("Disconnected")

if __name__ == "__main__":
    main()
