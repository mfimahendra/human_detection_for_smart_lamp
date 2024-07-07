import torch
import cv2
import numpy as np
import json
import mysql.connector
import threading


# Database connection parameters
config = {
    "user": "root",
    "password": "",
    "host": "localhost",
    "database": "iot",
    "raise_on_warnings": True
}

# Establish a database connection
conn = mysql.connector.connect(**config)

# Create a cursor object
cursor = conn.cursor()

# Execute a query
cursor.execute("SELECT * FROM lamp")

# Fetch all rows from the last executed query
rows = cursor.fetchall()



# Load the YOLOv5 model
model = torch.hub.load("ultralytics/yolov5", "yolov5s")

# Initialize the webcam
vid = cv2.VideoCapture(0)

# predefined_boxes = {
#     0: {
#         "points": [[100, 100], [400, 100], [500, 300], [100, 300]],
#         "callback": callback_box1
#     },
#     1: {
#         "points": [(50, 50), (200, 50), (200, 150), (50, 150)],
#         "callback": callback_box2
#     },
#     2: {
#         "points": [(150, 150), (450, 150), (450, 350), (150, 350)],
#         "callback": callback_box3
#     }
# }

def toggle_lamp(lamp_id):
    # Do request to rasberrypi API
    pass

predefined_boxes = {}

# parse json data on column 3
for row in rows:
    points = json.loads(row[3])  # Parse the JSON string from the third column
    idx = row[0]
    predefined_boxes[idx] = {
        "points": points,
        "callback": lambda: toggle_lamp("20h")
    }

# Close the cursor and connection
cursor.close()
conn.close()

def is_point_inside_polygon(x, y, polygon):
    pts_array = np.array(polygon, np.int32).reshape((-1, 1, 2))
    result = cv2.pointPolygonTest(pts_array, (x, y), False)
    return result >= 0

while True:
    ret, frame = vid.read()
    if not ret:
        break
    
    # Perform inference on the frame
    results = model(frame)
    
    # Get the detected objects
    detections = results.xyxy[0].cpu().numpy()
    
    box_has_person = {key: False for key in predefined_boxes}
    
    # Draw all predefined boxes
    for idx, box_info in predefined_boxes.items():
        pts_array = np.array(box_info["points"], np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts_array], isClosed=True, color=(0, 255, 0), thickness=2)
    
    # Draw bounding boxes on the frame
    for detection in detections:
        x1, y1, x2, y2, confidence, class_id = detection
        
        # Filter for person class ID (0)
        if int(class_id) != 0:
            continue

        label = f"{results.names[int(class_id)]} {confidence:.2f}"
        
        # Calculate the center point of the bounding box
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Check if the center point is inside any of the predefined boxes
        for idx, box_info in predefined_boxes.items():
            if is_point_inside_polygon(center_x, center_y, box_info["points"]):
                box_has_person[idx] = True
                color = (255, 0, 0)  # Blue if center is inside any predefined box
                break
        else:
            color = (0, 0, 255)  # Red if center is outside all predefined boxes
        
        # Draw rectangle
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        
        # Draw label
        cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw the center point
        cv2.circle(frame, (int(center_x), int(center_y)), 5, color, -1)
    
    for idx, has_person in box_has_person.items():
        if has_person:
            pts_array = np.array(predefined_boxes[idx]["points"], np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts_array], isClosed=True, color=(0, 0, 255), thickness=3)
            # if its stay for 5 seconds, call the callback function
            predefined_boxes[idx]["callback"]() 
    
    # Display the frame with bounding boxes
    cv2.imshow("Lampu cosdown", frame)
    
    # Handle keyboard input to quit
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

# Release the webcam and close all OpenCV windows
vid.release()
cv2.destroyAllWindows()
