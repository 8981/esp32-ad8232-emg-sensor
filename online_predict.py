import serial
import joblib
from collections import deque

PORT = "COM3"   # как у тебя
BAUD = 115200

MODEL_FILE = "rest_fist_model.joblib"

model = joblib.load(MODEL_FILE)

# сглаживание: решение по последним N предсказаниям
N_SMOOTH = 5
hist = deque(maxlen=N_SMOOTH)

print(f"Online prediction started on {PORT}.")
print("Try REST / FIST. Press Ctrl+C to stop.\n")

def parse_line(line: str):
    """
    Ожидаем: idx,featAbs1,featAbs2,featAbs3,label
    Возвращаем (x1,x2,x3) или None
    """
    parts = line.strip().split(",")
    if len(parts) != 5:
        return None
    _, a, b, c, _lab = parts
    try:
        return [float(a), float(b), float(c)]
    except:
        return None

ser = serial.Serial(PORT, BAUD, timeout=1)
try:
    while True:
        line = ser.readline().decode(errors="ignore")
        if not line:
            continue

        x = parse_line(line)
        if x is None:
            continue

        pred = model.predict([x])[0]  # 0=rest, 1=fist
        hist.append(pred)

        # majority vote
        rest_cnt = sum(1 for p in hist if p == 0)
        fist_cnt = sum(1 for p in hist if p == 1)
        if fist_cnt > rest_cnt:
            decision = "FIST"
            out_label = 1
        else:
            decision = "REST"
            out_label = 0

        print(f"{decision} (pred={pred}, smooth={list(hist)})  feats={x}")
finally:
    ser.close()