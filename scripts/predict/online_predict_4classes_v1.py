import serial
import joblib
import math
import numpy as np

PORT = "COM3"
BAUD = 115200

MODEL_FILE = "../model/emg_4classes_model_v1.joblib"

NAMES = ["REST", "FIST", "WRIST_UP", "WRIST_DOWN"]

CONF_THRESHOLD = 0.55
MIN_HITS = 3

model = joblib.load(MODEL_FILE)

N = int(model.n_features_in_)
print(f"Model expects {N} features.")
print("Expected v2 feature count: 12")

if N != 12:
    raise ValueError("Wrong model: this script expects 12 v2 features.")

ser = serial.Serial(PORT, BAUD, timeout=1)

current_state = 0
candidate_state = None
hits = 0


def parse_line(line: str):
    parts = line.strip().split(",")

    if len(parts) != 14:
        return None

    try:
        feats = [float(parts[i]) for i in range(1, 13)]

        if not all(math.isfinite(v) for v in feats):
            return None

        return feats

    except Exception:
        return None


print("\nOnline 4-class EMG prediction started.")
print("Ctrl+C to stop.\n")

try:
    while True:
        line = ser.readline().decode(errors="ignore").strip()

        if not line:
            continue

        if line.startswith("idx,"):
            continue

        x = parse_line(line)

        if x is None:
            continue

        proba = model.predict_proba([x])[0]

        pred_class = int(np.argmax(proba))
        confidence = float(np.max(proba))

        if confidence >= CONF_THRESHOLD:
            if candidate_state == pred_class:
                hits += 1
            else:
                candidate_state = pred_class
                hits = 1
        else:
            candidate_state = None
            hits = 0

        if hits >= MIN_HITS:
            current_state = candidate_state
            hits = 0

        probs_str = " | ".join(
            f"{NAMES[i]}={proba[i]:.2f}" for i in range(len(NAMES))
        )

        print(
            f"STATE={NAMES[current_state]} | "
            f"candidate={NAMES[pred_class]} | "
            f"conf={confidence:.2f} | "
            f"hits={hits} | "
            f"{probs_str}"
        )

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    ser.close()