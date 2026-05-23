import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
import statistics
import socket
import json
import time

#from udp_vision_to_ros_node import UdpVisionToRosNode

# -----------------------------
# UDP settings
# -----------------------------
WSL_IP = "192.168.27.80"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_vision_data(visible: bool, x_mm: float = 0.0, z_mm: float = 0.0, width_mm: float = 0.0):
    payload = {
        "visible": bool(visible),
        "x_mm": float(x_mm),
        "z_mm": float(z_mm),
        "width_mm": float(width_mm),
        "timestamp": time.time(),
    }

    data = json.dumps(payload).encode("utf-8")
    sock.sendto(data, (WSL_IP, UDP_PORT))


# -----------------------------
# Initialization
# -----------------------------
model = YOLO("yolov8n-seg.pt")

# In Windows this may be 0 or 1.
# Use the index that worked in your old script.
cap = cv2.VideoCapture(0)

z_history = deque(maxlen=20)
x_history = deque(maxlen=20)
w_history = deque(maxlen=20)

# -----------------------------
# Calibrated constants
# -----------------------------
BOTTLE_REAL_W = 70.0
FOCAL_LENGTH = 602


def get_stable_value(buffer):
    if len(buffer) < 5:
        return None
    return statistics.median(buffer)


while cap.isOpened():
    success, frame = cap.read()

    if not success:
        send_vision_data(False)
        break

    h_frame, w_frame, _ = frame.shape
    cam_center_x = w_frame / 2

    results = model.predict(
        frame,
        conf=0.5,
        classes=[39],
        verbose=False,
    )

    object_found = False

    if results[0].boxes is not None and len(results[0].boxes) > 0:
        best_box = None
        max_area = 0

        for box in results[0].boxes.xyxy.cpu().numpy():
            area = (box[2] - box[0]) * (box[3] - box[1])

            if area > max_area:
                max_area = area
                best_box = box

        if best_box is not None:
            object_found = True

            x1, y1, x2, y2 = best_box
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            pixel_w_box = x2 - x1

            # -----------------------------
            # Distance Z
            # -----------------------------
            dist_from_center = abs(cx - cam_center_x) / cam_center_x
            correction = 1 + (dist_from_center ** 2 * 0.1)
            corrected_pixel_w = pixel_w_box * correction

            current_z = (BOTTLE_REAL_W * FOCAL_LENGTH) / corrected_pixel_w
            z_history.append(current_z)
            avg_z = get_stable_value(z_history)

            if avg_z is not None:
                # -----------------------------
                # Horizontal offset X
                # Positive = object is right from camera center
                # Negative = object is left from camera center
                # -----------------------------
                current_x = ((cx - cam_center_x) * avg_z) / FOCAL_LENGTH
                x_history.append(current_x)
                avg_x = get_stable_value(x_history)

                avg_w = 0.0

                if results[0].masks is not None:
                    mask_points = results[0].masks.xy[0].astype(np.int32)
                    rect = cv2.minAreaRect(mask_points)
                    (_, _), (rw, rh), angle = rect

                    pixel_w_mask = min(rw, rh)
                    calc_w_mm = (pixel_w_mask * avg_z) / FOCAL_LENGTH

                    w_history.append(calc_w_mm)
                    stable_w = get_stable_value(w_history)

                    if stable_w is not None:
                        avg_w = stable_w

                    color = (0, 255, 0) if avg_z < 300 else (0, 255, 255)

                    cv2.polylines(frame, [mask_points], True, color, 2)
                else:
                    color = (0, 255, 0) if avg_z < 300 else (0, 255, 255)

                if avg_x is not None:
                    send_vision_data(
                        visible=True,
                        x_mm=avg_x,
                        z_mm=avg_z,
                        width_mm=avg_w,
                    )

                    cv2.drawMarker(
                        frame,
                        (int(cx), int(cy)),
                        color,
                        cv2.MARKER_CROSS,
                        20,
                        2,
                    )

                    label = (
                        f"DIST: {int(avg_z)}mm | "
                        f"SIDE: {int(avg_x)}mm | "
                        f"WIDTH: {int(avg_w)}mm"
                    )

                    cv2.rectangle(
                        frame,
                        (int(x1), int(y1) - 30),
                        (int(x1) + 390, int(y1)),
                        (0, 0, 0),
                        -1,
                    )

                    cv2.putText(
                        frame,
                        label,
                        (int(x1) + 5, int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        1,
                    )

                    cv2.rectangle(
                        frame,
                        (int(x1), int(y1)),
                        (int(x2), int(y2)),
                        color,
                        2,
                    )

    if not object_found:
        send_vision_data(False)

        cv2.putText(
            frame,
            "NO TARGET",
            (20, 80),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            (0, 0, 255),
            1,
        )

    # UI Overlay
    cv2.line(
        frame,
        (int(cam_center_x), 0),
        (int(cam_center_x), h_frame),
        (255, 0, 0),
        1,
    )

    cv2.putText(
        frame,
        "ROBOT VISION UDP ACTIVE",
        (20, 40),
        cv2.FONT_HERSHEY_DUPLEX,
        0.7,
        (255, 255, 255),
        1,
    )

    cv2.imshow("Robot Vision UDP Tracker", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

send_vision_data(False)

cap.release()
cv2.destroyAllWindows()
sock.close()