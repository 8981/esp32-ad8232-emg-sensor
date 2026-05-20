import time

from stservo_controller import STServoController


DEVICE = "/dev/ttyACM0"
SERVO_ID = 6

OPEN_POSITION = 2700
CLOSE_POSITION = 1500


def main():
    controller = STServoController(
        device=DEVICE,
        servo_id=SERVO_ID,
        open_position=OPEN_POSITION,
        close_position=CLOSE_POSITION,
        speed=800,
        acc=30,
    )

    try:
        controller.connect()

        print("Opening hand...")
        controller.open_hand()
        time.sleep(2)

        print("Closing hand...")
        controller.close_hand()
        time.sleep(2)

        print("Opening hand again...")
        controller.open_hand()
        time.sleep(2)

    finally:
        controller.disconnect()


if __name__ == "__main__":
    main()