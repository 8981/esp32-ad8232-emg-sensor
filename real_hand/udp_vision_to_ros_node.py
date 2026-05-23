import json
import socket

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float64


class UdpVisionToRosNode(Node):
    def __init__(self):
        super().__init__("udp_vision_to_ros_node")

        self.visible_pub = self.create_publisher(
            Bool,
            "/vision/object_visible",
            10,
        )

        self.x_pub = self.create_publisher(
            Float64,
            "/vision/object_x_mm",
            10,
        )

        self.distance_pub = self.create_publisher(
            Float64,
            "/vision/object_distance_mm",
            10,
        )

        self.udp_host = "0.0.0.0"
        self.udp_port = 5005

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.udp_host, self.udp_port))
        self.sock.setblocking(False)

        self.timer = self.create_timer(0.02, self.read_udp)

        self.get_logger().info("UDP Vision → ROS2 bridge started.")
        self.get_logger().info(f"Listening UDP on port {self.udp_port}")
        self.get_logger().info("Publishing:")
        self.get_logger().info("  /vision/object_visible")
        self.get_logger().info("  /vision/object_x_mm")
        self.get_logger().info("  /vision/object_distance_mm")

    def read_udp(self):
        while True:
            try:
                data, _ = self.sock.recvfrom(4096)
            except BlockingIOError:
                break

            try:
                payload = json.loads(data.decode("utf-8"))

                visible = bool(payload.get("visible", False))
                x_mm = float(payload.get("x_mm", 0.0))
                z_mm = float(payload.get("z_mm", 0.0))

                visible_msg = Bool()
                visible_msg.data = visible
                self.visible_pub.publish(visible_msg)

                x_msg = Float64()
                x_msg.data = x_mm
                self.x_pub.publish(x_msg)

                z_msg = Float64()
                z_msg.data = z_mm
                self.distance_pub.publish(z_msg)

                self.get_logger().info(
                    f"Vision UDP: visible={visible} | x={x_mm:.1f} mm | z={z_mm:.1f} mm"
                )

            except Exception as e:
                self.get_logger().warn(f"Failed to parse UDP packet: {e}")

    def destroy_node(self):
        try:
            self.sock.close()
        except Exception:
            pass

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = UdpVisionToRosNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()