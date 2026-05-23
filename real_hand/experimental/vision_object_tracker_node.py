import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
import statistics

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float64


class VisionObjectTrackerNode(Node):
    def __init__(self):
        super().__init__("vision_object_tracker_node")

        # -----------------------------
        # ROS publishers
        # -----------------------------
        self.visible_pub = self.create_publisher(
            Bool,
            "/vision/object_visible",
            10,
        )

        self.x_mm_pub = self.create_publisher(
            Float64,
            "/vision/object_x_mm",
            10,
        )

        self.distance_pub = self.create_publisher(
            Float64,
            "/vision/object_distance_mm",
            10,
        )

        # -----------------------------
        # YOLO model
        # -----------------------------
        self.model = YOLO("yolov8n-seg.pt")

        # COCO class id:
        # 39 = bottle
        self.object_class_id = 39

        # -----------------------------
        # Camera
        # -----------------------------
        # Change this if needed:
        # 0 = first camera
        # 1 = second camera
        self.camera_index = 1

        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Could not open camera index {self.camera_index}"
            )

        # -----------------------------
        # Filters
        # -----------------------------
        self.z_history = deque(maxlen=20)
        self.x_history = deque(maxlen=20)
        self.w_history = deque(maxlen=20)

        # -----------------------------
        # Calibrated constants
        # -----------------------------
        self.bottle_real_w_mm = 70.0
        self.focal_length_px = 602.0

        self.conf_threshold = 0.5

        self.get_logger().info("Vision object tracker started.")
        self.get_logger().info("Publishing:")
        self.get_logger().info("  /vision/object_visible")
        self.get_logger().info("  /vision/object_x_mm")
        self.get_logger().info("  /vision/object_distance_mm")
        self.get_logger().info("Press 'q' in camera window to exit.")

    def get_stable_value(self, buffer):
        if len(buffer) < 5:
            return None
        return statistics.median(buffer)

    def publish_visible(self, visible: bool):
        msg = Bool()
        msg.data = bool(visible)
        self.visible_pub.publish(msg)

    def publish_float(self, publisher, value: float):
        msg = Float64()
        msg.data = float(value)
        publisher.publish(msg)

    def run(self):
        while rclpy.ok() and self.cap.isOpened():
            success, frame = self.cap.read()

            if not success:
                self.get_logger().warn("Failed to read camera frame.")
                break

            h_frame, w_frame, _ = frame.shape
            cam_center_x = w_frame / 2.0

            results = self.model.predict(
                frame,
                conf=self.conf_threshold,
                classes=[self.object_class_id],
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
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    pixel_w_box = x2 - x1

                    # -----------------------------
                    # Z distance estimation
                    # -----------------------------
                    dist_from_center = abs(cx - cam_center_x) / cam_center_x
                    correction = 1.0 + (dist_from_center ** 2 * 0.1)
                    corrected_pixel_w = pixel_w_box * correction

                    current_z = (
                        self.bottle_real_w_mm * self.focal_length_px
                    ) / corrected_pixel_w

                    self.z_history.append(current_z)
                    avg_z = self.get_stable_value(self.z_history)

                    if avg_z is not None:
                        # -----------------------------
                        # X offset in mm
                        # Positive = object is right from camera center
                        # Negative = object is left from camera center
                        # -----------------------------
                        current_x = ((cx - cam_center_x) * avg_z) / self.focal_length_px

                        self.x_history.append(current_x)
                        avg_x = self.get_stable_value(self.x_history)

                        if avg_x is not None:
                            self.publish_visible(True)
                            self.publish_float(self.x_mm_pub, avg_x)
                            self.publish_float(self.distance_pub, avg_z)

                            self.get_logger().info(
                                f"Object: x={avg_x:.1f} mm | z={avg_z:.1f} mm"
                            )

                        # -----------------------------
                        # Width from mask
                        # -----------------------------
                        avg_w = 0.0

                        if results[0].masks is not None:
                            mask_points = results[0].masks.xy[0].astype(np.int32)
                            rect = cv2.minAreaRect(mask_points)
                            (_, _), (rw, rh), _ = rect

                            pixel_w_mask = min(rw, rh)
                            calc_w_mm = (pixel_w_mask * avg_z) / self.focal_length_px

                            self.w_history.append(calc_w_mm)
                            stable_w = self.get_stable_value(self.w_history)

                            if stable_w is not None:
                                avg_w = stable_w

                            color = (0, 255, 0) if avg_z < 300 else (0, 255, 255)

                            cv2.polylines(frame, [mask_points], True, color, 2)
                        else:
                            color = (0, 255, 0) if avg_z < 300 else (0, 255, 255)

                        # -----------------------------
                        # Visuals
                        # -----------------------------
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
                            f"SIDE: {int(avg_x) if avg_x is not None else 0}mm | "
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
                self.publish_visible(False)

                cv2.putText(
                    frame,
                    "NO TARGET",
                    (20, 80),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.7,
                    (0, 0, 255),
                    1,
                )

            # UI overlay
            cv2.line(
                frame,
                (int(cam_center_x), 0),
                (int(cam_center_x), h_frame),
                (255, 0, 0),
                1,
            )

            cv2.putText(
                frame,
                "ROBOT VISION TRACKER ACTIVE",
                (20, 40),
                cv2.FONT_HERSHEY_DUPLEX,
                0.7,
                (255, 255, 255),
                1,
            )

            cv2.imshow("Robot Vision Object Tracker", frame)

            rclpy.spin_once(self, timeout_sec=0.001)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.publish_visible(False)
        self.cap.release()
        cv2.destroyAllWindows()


def main(args=None):
    rclpy.init(args=args)

    node = VisionObjectTrackerNode()

    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_visible(False)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()