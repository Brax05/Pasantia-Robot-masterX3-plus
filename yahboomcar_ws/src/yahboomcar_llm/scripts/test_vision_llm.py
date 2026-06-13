import os
import sys
import argparse
import requests
import json
import time
import base64

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

def bbox_position(x1, x2, frame_width):
    center_x = (x1 + x2) / 2.0
    if center_x < frame_width * 0.33:
        return "izquierda"
    elif center_x < frame_width * 0.66:
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
        
        # Estimate width/size of bounding box as fraction of screen width
        width_ratio = round((x2 - x1) / frame_width, 2)

        detections.append({
            "objeto": name,
            "confianza": round(conf, 2),
            "posicion": pos,
            "tamaño_pantalla_ratio": width_ratio
        })

    # Sort by confidence descending and limit to top 8 detections
    detections.sort(key=lambda d: d["confianza"], reverse=True)
    return detections[:8]

def decide_movement(detections):
    if not detections:
        scene_text = "No se detecta ningún obstáculo u objeto en la cámara frente al robot. El camino está despejado."
    else:
        bullet_list = "\n".join(
            "- {} en posición {}, cubriendo un {} de la pantalla".format(
                d['objeto'], d['posicion'], d['tamaño_pantalla_ratio']
            )
            for d in detections
        )
        scene_text = "La cámara detecta los siguientes objetos:\n" + bullet_list

    print("\n[+] Descripción de escena:")
    print(scene_text)

    # Default: path is clear, move forward
    action = "forward"
    linear_speed = 0.25
    angular_speed = 0.0
    reason = "El camino está despejado, avanzando."

    # Look for obstacles (like person, chair, or anything in the center with screen ratio > 0.2)
    center_obstacles = [d for d in detections if d["posicion"] == "centro" and d["tamaño_pantalla_ratio"] > 0.2]
    
    if center_obstacles:
        # Check if there is a person
        people = [d for d in center_obstacles if d["objeto"] == "person"]
        if people:
            action = "stop"
            linear_speed = 0.0
            angular_speed = 0.0
            reason = "Obstáculo detectado: Persona en el centro. Deteniendo robot por seguridad."
        else:
            # Other obstacle in center, try to turn left/right to avoid it
            left_obstacles = [d for d in detections if d["posicion"] == "izquierda"]
            right_obstacles = [d for d in detections if d["posicion"] == "derecha"]
            
            action = "left" if len(right_obstacles) >= len(left_obstacles) else "right"
            linear_speed = 0.0
            angular_speed = 0.5 if action == "left" else -0.5
            reason = "Obstáculo detectado en el centro. Girando a la {} para esquivarlo.".format(
                "izquierda" if action == "left" else "derecha"
            )

    decision = {
        "accion": action,
        "velocidad_lineal": linear_speed,
        "velocidad_angular": angular_speed,
        "razon": reason
    }
    return json.dumps(decision, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Script de prueba aislada de YOLO + Llama 3.2 sin necesidad de ROS")
    parser.add_argument("--image", type=str, help="Ruta a una imagen estática para procesar con YOLO")
    parser.add_argument("--webcam", action="store_true", help="Usar la webcam local para capturar y procesar frames")
    parser.add_argument("--mock", action="store_true", help="Usar detecciones simuladas (sin YOLO/OpenCV) para probar el LLM directamente")
    parser.add_argument("--model", type=str, default="llama3.2", help="Nombre del modelo Ollama registrado (default: llama3.2)")
    parser.add_argument("--url", type=str, default="http://localhost:11434/api/chat", help="URL de la API de Ollama")
    parser.add_argument("--interval", type=float, default=0.0, help="Intervalo en segundos para capturar e inferir automáticamente (ej: 3.0). Si es 0.0, requiere presionar ESPACIO.")
    
    args = parser.parse_args()

    # Mode selection logic
    if args.mock:
        print("[*] Modo SIMULACIÓN activado. Enviando detecciones de prueba al LLM...")
        mock_detections = [
            {"objeto": "person", "confianza": 0.89, "posicion": "centro", "tamaño_pantalla_ratio": 0.35},
            {"objeto": "chair", "confianza": 0.72, "posicion": "derecha", "tamaño_pantalla_ratio": 0.15}
        ]
        decision = decide_movement(mock_detections)
        print("\n=== Decisión del LLM ===")
        print(decision)
        return

    # Check dependencies
    if cv2 is None or YOLO is None:
        print("[-] Error: Las librerías 'opencv-python' y/o 'ultralytics' no están instaladas.")
        print("    Puedes instalarlas ejecutando: pip install opencv-python ultralytics")
        print("    O puedes probar el LLM directamente ejecutando este script con: python test_vision_llm.py --mock")
        sys.exit(1)

    print("[*] Cargando modelo YOLO (yolo11n.pt)...")
    model = YOLO("yolo11n.pt")

    if args.image:
        if not os.path.exists(args.image):
            print("[-] Error: El archivo de imagen '{}' no existe.".format(args.image))
            sys.exit(1)
        
        print("[*] Leyendo imagen: {}".format(args.image))
        frame = cv2.imread(args.image)
        if frame is None:
            print("[-] Error al decodificar la imagen.")
            sys.exit(1)
            
        frame_width = frame.shape[1]
        results = model(frame, conf=0.45, verbose=False)
        detections = build_scene_description(results[0], model.names, frame_width)
        
        # Plot YOLO boxes and send to local Flask server
        annotated_frame = results[0].plot()
        try:
            _, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            flask_update_url = "http://localhost:5000/api/vision/update"
            requests.post(flask_update_url, json={
                "detections": detections,
                "frame": frame_b64
            }, timeout=1.0)
        except Exception:
            pass

        print("[+] Detecciones YOLO encontradas: {}".format(detections))
        decision = decide_movement(detections)
        print("\n=== Decisión del LLM ===")
        print(decision)

    elif args.webcam:
        if args.interval > 0:
            print("[*] Iniciando webcam local. Captura AUTOMÁTICA activa cada {} segundos.".format(args.interval))
            print("    (Presiona 'Q' en la ventana de video para salir)")
        else:
            print("[*] Iniciando webcam local. Presiona ESPACIO para capturar e inferir, o 'Q' para salir.")
            
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[-] Error: No se pudo abrir la webcam local.")
            sys.exit(1)

        last_query_time = 0.0
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[-] Error al leer de la webcam.")
                break

            current_time = time.time()
            auto_trigger = False
            
            # Check if interval elapsed for automatic capture
            if args.interval > 0 and (current_time - last_query_time >= args.interval):
                auto_trigger = True
                last_query_time = current_time

            # Show live preview
            preview_title = "Prueba de Vision Robot - Vista Previa (ESPACIO para manual / Q para salir)"
            if args.interval > 0:
                preview_title = "Prueba de Vision Robot - AUTOMÁTICO cada {}s (Q para salir)".format(args.interval)
                
            cv2.imshow(preview_title, frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            
            if key == 32 or auto_trigger: # Spacebar or automatic trigger
                print("\n[+] Capturando frame y corriendo YOLO...")
                frame_width = frame.shape[1]
                results = model(frame, conf=0.45, verbose=False)
                detections = build_scene_description(results[0], model.names, frame_width)
                
                # Draw boxes for visual feedback
                annotated_frame = results[0].plot()
                cv2.imshow("Captura Procesada", annotated_frame)

                # Encode and send to Flask local stream for Web GUI
                try:
                    _, buffer = cv2.imencode('.jpg', annotated_frame)
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    flask_update_url = "http://localhost:5000/api/vision/update"
                    requests.post(flask_update_url, json={
                        "detections": detections,
                        "frame": frame_b64
                    }, timeout=1.0)
                except Exception:
                    pass
                
                print("[+] Detecciones YOLO: {}".format([d['objeto'] for d in detections]))
                decision = decide_movement(detections)
                print("\n=== Decisión del LLM ===")
                print(decision)
                
                if auto_trigger:
                    print("\n[*] Esperando {} segundos para la siguiente consulta automática...".format(args.interval))
                else:
                    print("\nPresiona ESPACIO en la ventana principal para otra captura...")

        cap.release()
        cv2.destroyAllWindows()
    else:
        print("[!] Por favor especifica un modo de ejecución:")
        print("    python test_vision_llm.py --mock          (Prueba solo el LLM con datos simulados)")
        print("    python test_vision_llm.py --image img.jpg (Prueba YOLO + LLM en una imagen)")
        print("    python test_vision_llm.py --webcam        (Usa tu webcam local interactiva en modo manual)")
        print("    python test_vision_llm.py --webcam --interval 3.0 (Usa tu webcam local interactiva en modo automático)")

if __name__ == '__main__':
    main()
