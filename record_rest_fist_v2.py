import serial, time, math

PORT = "COM3"
BAUD = 115200
OUT_CSV = "state_open_fist_v2.csv"

REST_S = 2.5
FIST_S = 2.5
CYCLES = 10

# v2 features: idx + 12 features + label = 14 cols
FEATURES = ["m1","s1","a1","p1","m2","s2","a2","p2","m3","s3","a3","p3"]

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(1.0)
ser.reset_input_buffer()

rows = []

def read_for(duration_s, wanted_label):
    end_t = time.time() + duration_s
    got = 0
    while time.time() < end_t:
        line = ser.readline().decode(errors="ignore").strip()
        if not line or line.startswith("idx,"):
            continue

        parts = line.split(",")
        if len(parts) != 14:
            continue

        try:
            feats = [float(parts[i]) for i in range(1, 13)]  # 12 values
            lab_in = int(float(parts[13]))  # label from ESP32 (not used)
            if not all(math.isfinite(v) for v in feats):
                continue

            # We trust our commanded label instead of ESP32 label:
            rows.append([*feats, wanted_label])
            got += 1
        except:
            pass
    return got

for c in range(CYCLES):
    print(f"\nCycle {c+1}/{CYCLES}: REST(open)")
    ser.write(b"r")
    n = read_for(REST_S, wanted_label=0)
    print("  captured:", n)

    print(f"Cycle {c+1}/{CYCLES}: FIST(closed)")
    ser.write(b"f")
    n = read_for(FIST_S, wanted_label=1)
    print("  captured:", n)

ser.close()

with open(OUT_CSV, "w", encoding="utf-8") as f:
    f.write(",".join(FEATURES) + ",label\n")
    for r in rows:
        f.write(",".join(map(str, r)) + "\n")

print("\nSaved:", OUT_CSV, "rows:", len(rows))