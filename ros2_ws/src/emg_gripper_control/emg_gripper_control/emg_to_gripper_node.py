import math
import serial
import joblib
import json
import time

import paho.mqtt.client as mqtt

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
        # ML model path
        # -----------------------------
        self.model_file = (
            "/mnt/d/Study/Sensormodalities/"
            "esp32-ad8232-emg-sensor/"
            "model/rest_fist_model_v2.joblib"
        )

        # -----------------------------
        # Gazebo gripper command topic
        # -----------------------------
        self.cmd_topic = "/gripper_controller/commands"

        self.open_value = 0.0
        self.close_value = 0.15

        # -----------------------------
        # MQTT settings
        # -----------------------------
        self.mqtt_host = "localhost"
        self.mqtt_port = 1883
        self.mqtt_topic = "emg/prediction"
        self.mqtt_client = mqtt.Client()
        self.mqtt_enabled = False

        try:
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_enabled = True
            self.get_logger().info(
                f"MQTT connected: {self.mqtt_host}:{self.mqtt_port}, topic={self.mqtt_topic}"
            )
        except Exception as e:
            self.get_logger().warn(f"MQTT connection failed: {e}")

        # -----------------------------
        # Prediction smoothing
        # -----------------------------
        self.alpha = 0.2
        self.th_fist = 0.62
        self.th_rest = 0.48
        self.min_hits = 3

        self.state = 0
        self.hits = 0
        self.ema_p_fist = 0.0

        # -----------------------------
        # ROS publisher
        # -----------------------------
        self.pub = self.create_publisher(
            Float64MultiArray,
            self.cmd_topic,
            10
        )

        # -----------------------------
        # Load model
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

        # -----------------------------
        # Open serial
        # -----------------------------
        self.ser = serial.Serial(self.port, self.baud, timeout=0.05)
        self.ser.reset_input_buffer()

        self.get_logger().info(f"Opened serial port: {self.port}")

        self.publish_gripper(self.open_value)

        # Timer loop: 100 Hz
        self.timer = self.create_timer(0.01, self.update)

    def parse_line(self, line: str):
        parts = line.strip().split(",")

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

    def publish_mqtt_event(
        self,
        decision: str,
        label: int,
        command_value: float,
        p_rest: float,
        p_fist: float,
        features
    ):
        if not self.mqtt_enabled:
            return

        payload = {
            "prediction": decision,
            "label": int(label),
            "command_value": float(command_value),
            "p_rest": float(p_rest),
            "p_fist": float(p_fist),
            "ema_fist": float(self.ema_p_fist),
            "features": features,
            "feature_count": len(features),
            "timestamp": time.time()
        }

        self.mqtt_client.publish(
            self.mqtt_topic,
            json.dumps(payload)
        )

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

        p_rest = float(proba[0])
        p_fist = float(proba[1])

        self.ema_p_fist = (
            self.alpha * p_fist
            + (1.0 - self.alpha) * self.ema_p_fist
        )

        if self.state == 0:
            cond = self.ema_p_fist >= self.th_fist
        else:
            cond = self.ema_p_fist <= self.th_rest

        if cond:
            self.hits += 1
        else:
            self.hits = 0

        changed = False

        if self.hits >= self.min_hits:
            self.state = 1 - self.state
            self.hits = 0
            changed = True

        if self.state == 0:
            decision = "REST"
            command_value = self.open_value
        else:
            decision = "FIST"
            command_value = self.close_value

        self.publish_gripper(command_value)

        if changed:
            self.get_logger().info(
                f"State changed: {decision} | "
                f"p_rest={p_rest:.3f} | "
                f"p_fist={p_fist:.3f} | "
                f"ema_fist={self.ema_p_fist:.3f} | "
                f"cmd={command_value:.3f}"
            )

            self.publish_mqtt_event(
                decision=decision,
                label=self.state,
                command_value=command_value,
                p_rest=p_rest,
                p_fist=p_fist,
                features=x
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