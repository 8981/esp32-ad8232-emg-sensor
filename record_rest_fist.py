import serial, time

PORT = "COM3"     # <-- измени на свой
BAUD = 115200
OUT_CSV = "emg_rest_fist.csv"

REST_S = 3.0
FIST_S = 3.0
CYCLES = 8

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(1.0)

lines = []
header = None

def read_valid_line():
    # читаем пока не получим строку с 5 колонками
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue
        if line.startswith("idx,"):
            return None  # header/разметка
        parts = line.split(",")
        if len(parts) == 5:
            return line

for cyc in range(CYCLES):
    # REST
    ser.write(b"r")
    t_end = time.time() + REST_S
    while time.time() < t_end:
        line = read_valid_line()
        if line is None:
            continue
        lines.append(line)

    # FIST
    ser.write(b"f")
    t_end = time.time() + FIST_S
    while time.time() < t_end:
        line = read_valid_line()
        if line is None:
            continue
        lines.append(line)

ser.close()

# Запишем CSV
with open(OUT_CSV, "w", encoding="utf-8") as f:
    f.write("idx,featAbs1,featAbs2,featAbs3,label\n")
    for ln in lines:
        f.write(ln + "\n")

print("Saved:", OUT_CSV, "rows:", len(lines))