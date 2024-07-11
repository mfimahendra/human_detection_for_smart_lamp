import torch
import cv2
import numpy as np
import json
import mysql.connector
import threading
import requests
import time
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

location = "Lobby"

# Database connection parameters
config = {
    "user": "ympimis",
    "password": "ympimis",
    "host": "10.109.52.21",
    "database": "ympimis_2",
    "raise_on_warnings": True
}

# Establish a database connection
conn = mysql.connector.connect(**config)

# Create a cursor object
cursor = conn.cursor()

# Execute a query
cursor.execute("SELECT * FROM iot_lamps WHERE location = %s", (location,))

# Fetch all rows from the last executed query
rows = cursor.fetchall()

# Load the YOLOv5 model
model = torch.hub.load("ultralytics/yolov5", "yolov5s")

def get_session():
    session = requests.Session()
    retries = Retry(total=5,  # Jumlah total retry
                    backoff_factor=0.3,  # Faktor backoff untuk jeda retry
                    status_forcelist=[500, 502, 503, 504])  # Status HTTP untuk retry
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session

session = get_session()

predefined_boxes = {}

for row in rows:    
    ip_camera = row[2]    
    ip_controller = row[3]
    points = json.loads(row[5])  # Parse the JSON string from the third column
    idx = row[0]    
    predefined_boxes[idx] = {
        "points": points,
        "callback": lambda: toggle_lamp(idx, 'on')
    }


def toggle_lamp(lamp_id, state):    
    url = f"http://" + ip_controller + f"/lamp/{lamp_id}/{state}"
    # url = "http://" + ip_controller + f"/lamp/{lamp_id}/{state}"
    try:
        response = session.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print(f"Successfully toggled lamp {lamp_id} to {state}")
    except requests.RequestException as e:
        print(f"Failed to toggle lamp {lamp_id}: {e}")

# Initialize the webcam
vid = cv2.VideoCapture(ip_camera)

# Close the cursor and connection
cursor.close()
conn.close()

def is_point_inside_polygon(x, y, polygon):
    pts_array = np.array(polygon, np.int32).reshape((-1, 1, 2))
    result = cv2.pointPolygonTest(pts_array, (x, y), False)
    return result >= 0

last_request_time = time.time()
lamp_on = False

last_request_time = time.time()
lamp_on = False

last_request_time = {idx: time.time() for idx in predefined_boxes.keys()}
lamp_on = {idx: False for idx in predefined_boxes.keys()}

while True:
    try:
        ret, frame = vid.read()
        if not ret:
            break

        # Resize, convert color, and perform inference
        frame = cv2.resize(frame, (512, 384))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = model(frame)
        detections = results.xyxy[0].cpu().numpy()

        box_has_person = {key: False for key in predefined_boxes}

        for idx, box_info in predefined_boxes.items():
            pts_array = np.array(box_info["points"], np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts_array], isClosed=True, color=(0, 255, 0), thickness=2)

        person_detected_in_any_box = False
        for detection in detections:
            x1, y1, x2, y2, confidence, class_id = detection
            if int(class_id) != 0:
                continue

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            for idx, box_info in predefined_boxes.items():
                if is_point_inside_polygon(center_x, center_y, box_info["points"]):
                    box_has_person[idx] = True
                    person_detected_in_any_box = True
                    color = (255, 0, 0)
                    break
            else:
                color = (0, 0, 255)

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            label = f"{results.names[int(class_id)]} {confidence:.2f}"
            cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.circle(frame, (int(center_x), int(center_y)), 5, color, -1)

        for idx in predefined_boxes.keys():
            if box_has_person[idx]:
                if not lamp_on[idx]:
                    toggle_lamp(idx, 'on')
                    lamp_on[idx] = True
                last_request_time[idx] = time.time()
            else:
                if lamp_on[idx] and (time.time() - last_request_time[idx] > 5):
                    toggle_lamp(idx, 'off')
                    lamp_on[idx] = False

        cv2.imshow("Lampu", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    except Exception as e:
        # timeout 5second then try again
        print("Error: ", e)
        time.sleep(5)
        continue


# Release the webcam and close all OpenCV windows
vid.release()
cv2.destroyAllWindows()
