import serial
from serial.tools import list_ports

PORT = "COM3"   # <-- замени на тот порт, который нашёлся в шаге 1
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=2)
print("Reading lines from", PORT)

for _ in range(10):
    line = ser.readline().decode(errors="ignore").strip()
    print(line)

ser.close()