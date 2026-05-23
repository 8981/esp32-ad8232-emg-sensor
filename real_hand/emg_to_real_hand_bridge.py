import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, Bool

from stservo_controller import STServoController


class RealHandBridge(Node):
    def __init__(self):
        super().__init__("real_hand_bridge")

        # -----------------------------
        # Serial / STServo settings
        # -----------------------------
        self.device = "/dev/ttyACM0"

        # -----------------------------
        # Grip servo settings
        # -----------------------------
        self.grip_servo_id = 6

        # Use the values that work for your physical hand.
        # If the direction is wrong, swap them.
        self.open_position = 2700
        self.close_position = 2000

        # -----------------------------
        # Tracking servo settings
        # -----------------------------
        # This servo should rotate the camera/hand left-right.
        # Change ID if your horizontal axis servo has another ID.
        self.track_servo_id = 1

        self.track_center_position = 2048
        self.track_current_position = self.track_center_position

        self.track_min_position = 1500
        self.track_max_position = 2600

        # If tracking moves in the wrong direction, set this to -1.
        self.track_direction = 1

        # Object offset dead zone in mm.
        # If object is inside Â±20 mm, do not move.
        self.track_dead_zone_mm = 10.0

        # How aggressively servo reacts to object offset.
        self.track_gain = 0.08
        self.count = 0

        # Maximum servo step per update.
        self.track_max_step = 5

        self.track_min_step = 1

        # Latest vision state
        self.object_visible = False
        self.object_x_mm = 0.0

        # -----------------------------
        # Controller
        # -----------------------------
        self.controller = STServoController(
            device=self.device,
            servo_id=self.grip_servo_id,
            open_position=self.open_position,
            close_position=self.close_position,
            speed=800,
            acc=30,
        )

        self.controller.connect()

        # Safe initial state
        self.controller.open_hand()

        # Center tracking servo
        self.controller.move_servo(
            servo_id=self.track_servo_id,
            position=self.track_center_position,
            min_position=self.track_min_position,
            max_position=self.track_max_position,
            speed=150,
            acc=5,
        )

        self.last_grip = None

        # -----------------------------
        # ROS subscribers
        # -----------------------------
        self.grip_sub = self.create_subscription(
            Float64,
            "/robot_hand/grip_command",
            self.on_grip_command,
            10,
        )

        self.visible_sub = self.create_subscription(
            Bool,
            "/vision/object_visible",
            self.on_object_visible,
            10,
        )

        self.x_sub = self.create_subscription(
            Float64,
            "/vision/object_x_mm",
            self.on_object_x_mm,
            10,
        )

        # Tracking control loop, 10 Hz
        self.tracking_timer = self.create_timer(
            0.2,
            self.update_tracking,
        )

        self.get_logger().info("Real hand bridge started.")
        self.get_logger().info("Listening:")
        self.get_logger().info("  /robot_hand/grip_command")
        self.get_logger().info("  /vision/object_visible")
        self.get_logger().info("  /vision/object_x_mm")
        self.get_logger().info("EMG controls grip. Vision controls tracking.")

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

    def on_object_visible(self, msg: Bool):
        self.object_visible = bool(msg.data)

    def on_object_x_mm(self, msg: Float64):
        self.object_x_mm = float(msg.data)

    def update_tracking(self):
        if not self.object_visible:
            return

        offset = self.object_x_mm

        # Stop zone: object is centered enough
        if abs(offset) <= self.track_dead_zone_mm:
            self.get_logger().info(
                f"Tracking locked: x={offset:.1f} mm | servo={self.track_current_position}"
            )
            return

        # Proportional step, but limited
        raw_step = abs(offset) * self.track_gain
        step = int(min(self.track_max_step, max(self.track_min_step, raw_step)))

        # Positive offset means object is right from camera center.
        # Negative offset means object is left from camera center.
        if offset > 0:
            direction = 1
        else:
            direction = -1

        new_position = self.track_current_position + (
             direction * step
        )

        new_position = max(
            self.track_min_position,
            min(self.track_max_position, new_position),
        )

        # If position did not really change, do nothing
        if new_position == self.track_current_position:
            return

        self.track_current_position = new_position

        self.controller.move_servo(
            servo_id=self.track_servo_id,
            position=self.track_current_position,
            min_position=self.track_min_position,
            max_position=self.track_max_position,
            speed=250,
            acc=10,
        )

        self.get_logger().info(
            f"Tracking: x={offset:.1f} mm | "
            f"step={step} | "
            f"servo={self.track_current_position}"
        )

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