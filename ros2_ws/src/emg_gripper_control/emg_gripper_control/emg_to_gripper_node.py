import math
import serial
import joblib
import numpy as np

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray


class EmgToGripperNode(Node):
    def __init__(self):
        super().__init__("emg_to_gripper_node")

        # -----------------------------
        # Serial / ESP32 settings
        # -----------------------------
        self.port = "/dev/ttyUSB0"
        self.baud = 115200

        # -----------------------------
        # Four-class Random Forest model
        # -----------------------------
        self.model_file = (
            "/mnt/d/Study/Sensormodalities/"
            "esp32-ad8232-emg-sensor/"
            "model/"
            "emg_4classes_rf_model_v1.joblib"
        )

        self.class_names = [
            "REST",
            "FIST",
            "WRIST_UP",
            "WRIST_DOWN"
        ]

        # -----------------------------
        # Gazebo gripper command topic
        # -----------------------------
        self.cmd_topic = "/gripper_controller/commands"

        # In this Gazebo gripper model:
        # 0.0  = open
        # 0.15 = closed
        self.open_value = 0.0
        self.close_value = 0.15

        # -----------------------------
        # Multi-class decision parameters
        # -----------------------------
        self.conf_threshold = 0.45
        self.min_hits = 4

        self.current_state = 0
        self.candidate_state = None
        self.hits = 0

        # -----------------------------
        # ROS publisher
        # -----------------------------
        self.pub = self.create_publisher(
            Float64MultiArray,
            self.cmd_topic,
            10
        )

        # -----------------------------
        # Load ML model
        # -----------------------------
        self.model = joblib.load(self.model_file)

        n_features = int(self.model.n_features_in_)

        if n_features != 12:
            raise ValueError(
                f"Wrong model feature count: {n_features}. Expected 12."
            )

        self.get_logger().info(f"Loaded model: {self.model_file}")
        self.get_logger().info(f"Model expects {n_features} features.")
        self.get_logger().info(f"Publishing to: {self.cmd_topic}")
        self.get_logger().info("Experimental 4-class mode enabled.")
        self.get_logger().info("REST/FIST control the gripper. WRIST_UP/WRIST_DOWN are logged only.")

        # -----------------------------
        # Open Serial
        # -----------------------------
        self.ser = serial.Serial(self.port, self.baud, timeout=0.05)
        self.ser.reset_input_buffer()

        self.get_logger().info(f"Opened serial port: {self.port}")

        # Send initial open command
        self.publish_gripper(self.open_value)

        # Timer loop: 100 Hz
        self.timer = self.create_timer(0.01, self.update)

    def parse_line(self, line: str):
        parts = line.strip().split(",")

        # v2 format:
        # idx + 12 features + label = 14 columns
        if len(parts) != 14:
            return None

        try:
            feats = [float(parts[i]) for i in range(1, 13)]

            if not all(math.isfinite(v) for v in feats):
                return None

            return feats

        except Exception:
            return None

    def publish_gripper(self, value: float):
        msg = Float64MultiArray()
        msg.data = [float(value)]
        self.pub.publish(msg)

    def apply_state_to_gripper(self, state: int):
        """
        REST and FIST control the Gazebo gripper.
        WRIST_UP and WRIST_DOWN are recognized but not mapped to the demo gripper.
        """

        if state == 0:
            # REST
            self.publish_gripper(self.open_value)
            return self.open_value

        if state == 1:
            # FIST
            self.publish_gripper(self.close_value)
            return self.close_value

        # WRIST_UP / WRIST_DOWN:
        # no gripper command change in the current Gazebo demo
        return None

    def update(self):
        line = self.ser.readline().decode(errors="ignore").strip()

        if not line:
            return

        if line.startswith("idx,"):
            return

        x = self.parse_line(line)

        if x is None:
            return

        proba = self.model.predict_proba([x])[0]

        pred_class = int(np.argmax(proba))
        confidence = float(np.max(proba))

        if confidence >= self.conf_threshold:
            if self.candidate_state == pred_class:
                self.hits += 1
            else:
                self.candidate_state = pred_class
                self.hits = 1
        else:
            self.candidate_state = None
            self.hits = 0

        changed = False

        if self.hits >= self.min_hits:
            if self.current_state != self.candidate_state:
                self.current_state = self.candidate_state
                changed = True

            self.hits = 0

        if changed:
            command_value = self.apply_state_to_gripper(self.current_state)

            probs_str = " | ".join(
                f"{self.class_names[i]}={proba[i]:.2f}"
                for i in range(len(self.class_names))
            )

            if command_value is None:
                command_text = "no gripper command"
            else:
                command_text = f"cmd={command_value:.3f}"

            self.get_logger().info(
                f"State changed: {self.class_names[self.current_state]} | "
                f"conf={confidence:.2f} | "
                f"{command_text} | "
                f"{probs_str}"
            )

    def destroy_node(self):
        try:
            if hasattr(self, "ser") and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = EmgToGripperNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_gripper(node.open_value)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()