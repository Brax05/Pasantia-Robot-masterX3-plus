import time
import requests
import cv2
from ultralytics import YOLO

MODEL_PATH = "yolo11n.pt"
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/chat"
CAMERA_INDEX = 0
CONFIDENCE = 0.45
LLM_INTERVAL_SECONDS = 12
MAX_DETECTIONS_FOR_PROMPT = 8
WINDOW_NAME = "YOLO + LLM"


def bbox_position(x1, x2, frame_width):
    center_x = (x1 + x2) / 2
    if center_x < frame_width * 0.33:
        return "izquierda"
    if center_x < frame_width * 0.66:
        return "centro"
    return "derecha"


def build_scene_description(result, model_names, frame_width):
    detections = []
    boxes = result.boxes

    if boxes is None or len(boxes) == 0:
        return detections

    for box in boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        name = model_names[cls_id]
        pos = bbox_position(x1, x2, frame_width)
        detections.append(
            {
                "name": name,
                "confidence": round(conf, 2),
                "position": pos,
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            }
        )

    detections.sort(key=lambda d: d["confidence"], reverse=True)
    return detections[:MAX_DETECTIONS_FOR_PROMPT]


def ask_ollama(detections):
    if not detections:
        return "Sin objetos detectados relevantes."

    bullet_list = "\n".join(
        f"- objeto={d['name']}, confianza={d['confidence']}, posicion={d['position']}, bbox={d['bbox']}"
        for d in detections
    )

    system_prompt = (
        "Eres un asistente de robot movil. "
        "Responde en español, breve, claro y util para control robotico. "
        "No inventes objetos que no aparezcan en la lista."
    )

    user_prompt = (
        "Analiza esta escena detectada por YOLO desde una camara.\n"
        f"{bullet_list}\n\n"
        "Entrega exactamente este formato:\n"
        "1. Resumen: una frase corta de la escena.\n"
        "2. Riesgo: bajo, medio o alto.\n"
        "3. Accion sugerida: una accion concreta para un robot movil."
    )

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def main():
    print("Cargando modelo YOLO...")
    model = YOLO(MODEL_PATH)

    print("Abriendo camara...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la camara. Revisa el indice o permisos.")

    last_llm_time = 0
    latest_llm_text = "Esperando detecciones para consultar al LLM..."

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("No se pudo leer un frame de la camara.")
                break

            frame_height, frame_width = frame.shape[:2]
            results = model(frame, conf=CONFIDENCE, verbose=False)
            result = results[0]
            annotated = result.plot()

            detections = build_scene_description(result, model.names, frame_width)
            now = time.time()

            if now - last_llm_time >= LLM_INTERVAL_SECONDS:
                try:
                    latest_llm_text = ask_ollama(detections)
                    print("\n===== RESPUESTA LLM =====")
                    print(latest_llm_text)
                    print("=========================\n")
                except requests.RequestException as e:
                    latest_llm_text = f"Error consultando Ollama: {e}"
                    print(latest_llm_text)
                last_llm_time = now

            overlay_lines = [
                f"Modelo YOLO: {MODEL_PATH}",
                f"Modelo LLM: {OLLAMA_MODEL}",
                f"Detecciones: {len(detections)}",
                "LLM:",
            ]
            overlay_lines.extend(latest_llm_text.splitlines()[:6])

            y = 25
            for line in overlay_lines:
                cv2.putText(
                    annotated,
                    line,
                    (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )
                y += 25

            cv2.imshow(WINDOW_NAME, annotated)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

