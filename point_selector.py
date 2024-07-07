import cv2
import numpy as np

# Global variable to store points
points = []

def click_event(event, x, y, flags, param):
    # On left mouse button click, store the points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        # Draw the point on the frame
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        cv2.imshow("Frame", frame)
        
        # Draw the polyline if we have 4 points
        if len(points) == 4:
            cv2.polylines(frame, [np.array(points)], isClosed=True, color=(255, 0, 0), thickness=2)
            cv2.imshow("Frame", frame)
            print("Selected Points: ", points)
            # make data like this [[171,200],[429,203],[466,471],[157,465]]                                    

# Capture video from camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

cv2.namedWindow("Frame")
cv2.setMouseCallback("Frame", click_event)

while True:
    # Read frame from the camera
    ret, frame = cap.read()
    
    if not ret:
        print("Error: Failed to capture image")
        break
    
    # Display the frame
    cv2.imshow("Frame", frame)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q') or len(points) == 4:
        break

# Release the video capture object and close all windows
cap.release()
cv2.destroyAllWindows()

# Print the coordinates of the selected points
if len(points) == 4:
    for idx, point in enumerate(points):
        print(f"Point {idx + 1}: x = {point[0]}, y = {point[1]}")
else:
    print("Insufficient points selected.")
