import serial, joblib
import numpy as np

PORT = "COM3"
BAUD = 115200
MODEL_FILE = "rest_fist_model.joblib"

NAMES = ["REST", "FIST"]

model = joblib.load(MODEL_FILE)
N = int(model.n_features_in_)
print(f"Model expects {N} features (v2 = 12).")

ser = serial.Serial(PORT, BAUD, timeout=1)

# --- smoothing + hysteresis ---
ALPHA = 0.2          # EMA smoothing for p(FIST)
TH_FIST = 0.62      # switch REST->FIST only if confident
TH_REST = 0.48      # switch FIST->REST only if clearly confident for REST
MIN_HITS = 3        # require N consecutive satisfied decisions

state = 0  # 0 REST, 1 FIST
hits = 0

def parse_line(line: str):
    parts = line.strip().split(",")
    # v2 format: idx + 12 features + label => 14 columns
    if len(parts) != 14:
        return None
    try:
        # features are columns 1..12
        feats = [float(parts[i]) for i in range(1, 13)]
        return feats
    except:
        return None

ema_p_fist = 0.0

print("Online REST/FIST (hysteresis). Ctrl+C to stop.\n")

try:
    while True:
        line = ser.readline().decode(errors="ignore")
        if not line:
            continue
        x = parse_line(line)
        if x is None:
            continue

        proba = model.predict_proba([x])[0]   # [p_rest, p_fist]
        p_fist = float(proba[1])
        ema_p_fist = ALPHA * p_fist + (1 - ALPHA) * ema_p_fist

        # hysteresis decision
        if state == 0:  # REST -> FIST
            cond = ema_p_fist >= TH_FIST
        else:            # FIST -> REST
            cond = ema_p_fist <= TH_REST

        if cond:
            hits += 1
        else:
            hits = 0

        if hits >= MIN_HITS:
            state = 1 - state  # toggle
            hits = 0

        decision = NAMES[state]
        print(f"{decision} | p_fist={p_fist:.3f} ema={ema_p_fist:.3f} hits={hits}")
finally:
    ser.close()