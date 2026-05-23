import cv2

backends = [
    ("DSHOW", cv2.CAP_DSHOW),
    ("MSMF", cv2.CAP_MSMF),
    ("ANY", cv2.CAP_ANY),
]

for backend_name, backend in backends:
    print(f"\n=== Backend: {backend_name} ===")

    for index in range(5):
        cap = cv2.VideoCapture(index, backend)

        if cap.isOpened():
            ret, frame = cap.read()
            print(f"Camera index {index}: opened, frame={ret}")

            if ret:
                print(f"  shape: {frame.shape}")

            cap.release()
        else:
            print(f"Camera index {index}: not available")