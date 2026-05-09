import serial
import time
import math

PORT = "COM3"
BAUD = 115200

OUT_CSV = "emg_rest_fist_v2.csv"

REST_S = 2.5
FIST_S = 2.5
CYCLES = 10

FEATURES = [
    "m1", "s1", "a1", "p1",
    "m2", "s2", "a2", "p2",
    "m3", "s3", "a3", "p3"
]

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(1.0)
ser.reset_input_buffer()

rows = []

def read_for(duration_s, wanted_label):
    end_t = time.time() + duration_s
    got = 0

    while time.time() < end_t:
        line = ser.readline().decode(errors="ignore").strip()

        if not line:
            continue

        if line.startswith("idx,"):
            continue

        parts = line.split(",")

        # v2 format:
        # idx + 12 features + label = 14 columns
        if len(parts) != 14:
            continue

        try:
            feats = [float(parts[i]) for i in range(1, 13)]
            esp_label = int(float(parts[13]))

            if not all(math.isfinite(v) for v in feats):
                continue

            # We trust the label commanded from Python.
            # wanted_label = 0 for REST, 1 for FIST.
            rows.append([*feats, wanted_label])
            got += 1

        except Exception:
            continue

    return got

try:
    for c in range(CYCLES):
        print(f"\nCycle {c + 1}/{CYCLES}: REST / open hand")
        ser.write(b"r")
        n = read_for(REST_S, wanted_label=0)
        print("  captured:", n)

        print(f"Cycle {c + 1}/{CYCLES}: FIST / closed hand")
        ser.write(b"f")
        n = read_for(FIST_S, wanted_label=1)
        print("  captured:", n)

    ser.write(b"n")

finally:
    ser.close()

with open(OUT_CSV, "w", encoding="utf-8") as f:
    f.write(",".join(FEATURES) + ",label\n")

    for r in rows:
        f.write(",".join(map(str, r)) + "\n")

print("\nSaved:", OUT_CSV)
print("Rows:", len(rows))

if len(rows) == 0:
    print("\nWARNING: Dataset is empty. Check Serial format and COM port.")