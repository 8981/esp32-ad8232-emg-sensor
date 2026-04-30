import serial, time, math

PORT = "COM3"   # как у тебя: COM3
BAUD = 115200
OUT_CSV = "emg_rest_fist.csv"

REST_S = 3.0
FIST_S = 3.0
CYCLES = 6

ser = serial.Serial(PORT, BAUD, timeout=0.5)
time.sleep(1.0)

ser.reset_input_buffer()

lines = []
header = None

def read_lines_for_duration(seconds):
    """Read as many valid lines as possible for given duration."""
    end_t = time.time() + seconds
    accepted = 0
    last_label = None

    while time.time() < end_t:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue

        if line.startswith("idx,"):
            # header
            continue

        parts = line.split(",")
        if len(parts) != 5:
            continue

        idx, a, b, c, lab = parts
        try:
            fa = float(a); fb = float(b); fc = float(c); fl = int(float(lab))
            if not (math.isfinite(fa) and math.isfinite(fb) and math.isfinite(fc)):
                continue
        except:
            continue

        lines.append((idx, fa, fb, fc, fl))
        accepted += 1
        last_label = fl

    return accepted, last_label

print(f"Start recording on {PORT}. Close Serial Monitor!")

for cyc in range(CYCLES):
    print(f"\nCycle {cyc+1}/{CYCLES}: REST")
    ser.write(b"r")
    n, last_lab = read_lines_for_duration(REST_S)
    print(f"  captured: {n} samples, last label: {last_lab}")

    print(f"Cycle {cyc+1}/{CYCLES}: FIST")
    ser.write(b"f")
    n, last_lab = read_lines_for_duration(FIST_S)
    print(f"  captured: {n} samples, last label: {last_lab}")

ser.close()

with open(OUT_CSV, "w", encoding="utf-8") as f:
    f.write("idx,featAbs1,featAbs2,featAbs3,label\n")
    for (idx, fa, fb, fc, fl) in lines:
        f.write(f"{idx},{fa},{fb},{fc},{fl}\n")

print("\nSaved:", OUT_CSV, "rows:", len(lines))