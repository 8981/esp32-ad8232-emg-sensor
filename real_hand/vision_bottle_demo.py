import time

import cv2
from ultralytics import YOLO

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64


class BottleVisionGraspNode(Node):
    def __init__(self):
        super().__init__("bottle_vision_grasp_node")

        # -----------------------------
        # ROS publisher
        # -----------------------------
        self.grip_topic = "/robot_hand/grip_command"

        self.grip_pub = self.create_publisher(
            Float64,
            self.grip_topic,
            10,
        )

        # -----------------------------
        # YOLO settings
        # -----------------------------
        self.model = YOLO("yolov8n.pt")

        # COCO class id:
        # 39 = bottle
        self.bottle_class_id = 39

        self.conf_threshold = 0.5

        # -----------------------------
        # Camera settings
        # -----------------------------
        self.camera_index = 0
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera index {self.camera_index}")

        # -----------------------------
        # Grasp decision settings
        # -----------------------------
        self.center_tolerance = 0.15
        """
        Normalized offset tolerance.
        0.15 means the bottle center can be within ±15% of image center.
        """

        self.min_width_ratio = 0.18
        """
        Approximate distance threshold.
        If the bottle bounding box width is large enough,
        we assume it is close enough to grasp.
        """

        self.required_stable_frames = 5

        self.centered_frames = 0
        self.lost_frames = 0
        self.required_lost_frames = 10

        self.current_grip = None

        self.get_logger().info("Bottle vision grasp node started.")
        self.get_logger().info(f"Publishing grip commands to: {self.grip_topic}")
        self.get_logger().info("0.0 = open, 1.0 = close")
        self.get_logger().info("Press 'q' in camera window to exit.")

    def publish_grip(self, value: float):
        value = max(0.0, min(1.0, float(value)))

        if self.current_grip is not None and abs(value - self.current_grip) < 0.01:
            return

        self.current_grip = value

        msg = Float64()
        msg.data = value
        self.grip_pub.publish(msg)

        if value >= 0.9:
            self.get_logger().info("Grip command: CLOSE")
        else:
            self.get_logger().info("Grip command: OPEN")

    def run(self):
        # Safe initial state
        self.publish_grip(0.0)

        while rclpy.ok():
            ret, frame = self.cap.read()

            if not ret:
                self.get_logger().warn("Failed to read camera frame.")
                continue

            h, w = frame.shape[:2]
            image_center_x = w / 2.0

            results = self.model.predict(
                frame,
                conf=self.conf_threshold,
                classes=[self.bottle_class_id],
                verbose=False,
            )

            best_box = None
            best_conf = 0.0

            for result in results:
                if result.boxes is None:
                    continue

                for box in result.boxes:
                    conf = float(box.conf[0])

                    if conf > best_conf:
                        best_conf = conf
                        best_box = box

            bottle_detected = best_box is not None

            if bottle_detected:
                xyxy = best_box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy

                box_center_x = (x1 + x2) / 2.0
                box_width = x2 - x1

                offset_x = (box_center_x - image_center_x) / image_center_x
                width_ratio = box_width / float(w)

                is_centered = abs(offset_x) <= self.center_tolerance
                is_close_enough = width_ratio >= self.min_width_ratio

                if is_centered and is_close_enough:
                    self.centered_frames += 1
                else:
                    self.centered_frames = 0

                self.lost_frames = 0

                # Draw box
                color = (0, 255, 0) if is_centered else (0, 255, 255)
                cv2.rectangle(
                    frame,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    color,
                    2,
                )

                text = (
                    f"bottle conf={best_conf:.2f} "
                    f"offset={offset_x:.2f} "
                    f"width={width_ratio:.2f}"
                )

                cv2.putText(
                    frame,
                    text,
                    (int(x1), max(30, int(y1) - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                )

                if self.centered_frames >= self.required_stable_frames:
                    self.publish_grip(1.0)
                else:
                    self.publish_grip(0.0)

            else:
                self.centered_frames = 0
                self.lost_frames += 1

                if self.lost_frames >= self.required_lost_frames:
                    self.publish_grip(0.0)

                cv2.putText(
                    frame,
                    "No bottle detected",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2,
                )

            # Draw center zone
            left_limit = int(image_center_x * (1.0 - self.center_tolerance))
            right_limit = int(image_center_x * (1.0 + self.center_tolerance))

            cv2.line(frame, (left_limit, 0), (left_limit, h), (255, 0, 0), 2)
            cv2.line(frame, (right_limit, 0), (right_limit, h), (255, 0, 0), 2)

            cv2.imshow("Bottle Vision Grasp", frame)

            rclpy.spin_once(self, timeout_sec=0.001)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

        self.publish_grip(0.0)
        self.cap.release()
        cv2.destroyAllWindows()


def main(args=None):
    rclpy.init(args=args)

    node = BottleVisionGraspNode()

    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_grip(0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()