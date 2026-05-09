import serial
import joblib
import math

PORT = "COM3"
BAUD = 115200

MODEL_FILE = "rest_fist_model_v2.joblib"

NAMES = ["REST", "FIST"]

model = joblib.load(MODEL_FILE)

N = int(model.n_features_in_)
print(f"Model expects {N} features.")
print("Expected v2 feature count: 12")

if N != 12:
    raise ValueError("Wrong model: this script expects a model trained on 12 v2 features.")

ser = serial.Serial(PORT, BAUD, timeout=1)

# Smoothing + hysteresis
ALPHA = 0.2
TH_FIST = 0.62
TH_REST = 0.48
MIN_HITS = 3

state = 0  # 0 = REST, 1 = FIST
hits = 0
ema_p_fist = 0.0

def parse_line(line: str):
    parts = line.strip().split(",")

    # v2 format:
    # idx + 12 features + label = 14 columns
    if len(parts) != 14:
        return None

    try:
        feats = [float(parts[i]) for i in range(1, 13)]

        if not all(math.isfinite(v) for v in feats):
            return None

        return feats

    except Exception:
        return None

print("\nOnline REST/FIST prediction started.")
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

        p_rest = float(proba[0])
        p_fist = float(proba[1])

        ema_p_fist = ALPHA * p_fist + (1 - ALPHA) * ema_p_fist

        # Hysteresis decision
        if state == 0:
            # REST -> FIST
            cond = ema_p_fist >= TH_FIST
        else:
            # FIST -> REST
            cond = ema_p_fist <= TH_REST

        if cond:
            hits += 1
        else:
            hits = 0

        if hits >= MIN_HITS:
            state = 1 - state
            hits = 0

        decision = NAMES[state]

        print(
            f"{decision} | "
            f"p_rest={p_rest:.3f} | "
            f"p_fist={p_fist:.3f} | "
            f"ema_fist={ema_p_fist:.3f} | "
            f"hits={hits}"
        )

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    ser.close()