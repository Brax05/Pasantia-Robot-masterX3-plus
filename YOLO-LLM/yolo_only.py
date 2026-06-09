from ultralytics import YOLO
import cv2

MODEL_PATH = "yolo11n.pt"
CAMERA_INDEX = 0
CONFIDENCE = 0.45
WINDOW_NAME = "YOLO Webcam"

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la camara. Revisa el indice de camara o permisos.")

while True:
    ok, frame = cap.read()
    if not ok:
        print("No se pudo leer un frame de la camara.")
        break

    results = model(frame, conf=CONFIDENCE, verbose=False)
    annotated = results[0].plot()

    cv2.imshow(WINDOW_NAME, annotated)

    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()