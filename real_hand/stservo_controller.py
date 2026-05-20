import time

from scservo_sdk import PortHandler
from scservo_sdk.sms_sts import sms_sts


class STServoController:
    def __init__(
        self,
        device="/dev/ttyACM0",
        baudrate=1_000_000,
        servo_id=6,
        open_position=2000,
        close_position=2700,
        speed=800,
        acc=30,
    ):
        self.device = device
        self.baudrate = baudrate
        self.servo_id = servo_id

        self.open_position = open_position
        self.close_position = close_position

        self.speed = speed
        self.acc = acc

        self.port_handler = PortHandler(self.device)
        self.packet_handler = sms_sts(self.port_handler)

        self.connected = False

    def connect(self):
        if not self.port_handler.openPort():
            raise RuntimeError(f"Failed to open port: {self.device}")

        if not self.port_handler.setBaudRate(self.baudrate):
            raise RuntimeError(f"Failed to set baudrate: {self.baudrate}")

        self.connected = True
        print(f"Connected to STServo on {self.device} at {self.baudrate}")

    def disconnect(self):
        if self.connected:
            self.port_handler.closePort()
            self.connected = False
            print("Disconnected from STServo")

    def move_to(self, position: int):
        if not self.connected:
            raise RuntimeError("Controller is not connected")

        position = int(position)

        min_pos = min(self.open_position, self.close_position)
        max_pos = max(self.open_position, self.close_position)

        position = max(min_pos, min(max_pos, position))

        self.packet_handler.WritePosEx(
            self.servo_id,
            position,
            self.speed,
            self.acc,
        )

        print(f"Servo {self.servo_id} -> position {position}")

    def open_hand(self):
        self.move_to(self.open_position)

    def close_hand(self):
        self.move_to(self.close_position)

    def set_grip(self, value: float):
        """
        value:
          0.0 = open
          1.0 = closed
        """
        value = max(0.0, min(1.0, float(value)))

        position = self.open_position + value * (
            self.close_position - self.open_position
        )

        self.move_to(int(position))


if __name__ == "__main__":
    controller = STServoController(
        device="/dev/ttyACM0",
        servo_id=6,
        open_position=2000,
        close_position=2700,
    )

    try:
        controller.connect()

        controller.open_hand()
        time.sleep(2)

        controller.close_hand()
        time.sleep(2)

        controller.open_hand()
        time.sleep(2)

    finally:
        controller.disconnect()