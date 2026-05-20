import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

from stservo_controller import STServoController


class RealHandBridge(Node):
    def __init__(self):
        super().__init__("real_hand_bridge")

        # Change this if your servo controller uses another port
        self.device = "/dev/ttyACM0"

        self.servo_id = 6

        # Adjust these values for your real hand mechanics
        self.open_position = 2700
        self.close_position = 1500

        self.controller = STServoController(
            device=self.device,
            servo_id=self.servo_id,
            open_position=self.open_position,
            close_position=self.close_position,
            speed=800,
            acc=30,
        )

        self.controller.connect()

        # Safe initial state
        self.controller.open_hand()

        self.last_grip = None

        self.subscription = self.create_subscription(
            Float64,
            "/robot_hand/grip_command",
            self.on_grip_command,
            10,
        )

        self.get_logger().info("Real hand bridge started.")
        self.get_logger().info("Listening topic: /robot_hand/grip_command")
        self.get_logger().info("0.0 = open, 1.0 = close")

    def on_grip_command(self, msg: Float64):
        grip = float(msg.data)

        # Safety clamp
        grip = max(0.0, min(1.0, grip))

        # Avoid repeated identical commands
        if self.last_grip is not None and abs(grip - self.last_grip) < 0.01:
            return

        self.last_grip = grip

        self.get_logger().info(f"Received grip command: {grip:.2f}")

        self.controller.set_grip(grip)

    def destroy_node(self):
        try:
            self.get_logger().info("Opening hand before shutdown...")
            self.controller.open_hand()
            self.controller.disconnect()
        except Exception as e:
            self.get_logger().warn(f"Cleanup error: {e}")

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = RealHandBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()