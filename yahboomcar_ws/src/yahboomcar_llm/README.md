# yahboomcar_llm - Integración Llama 3.2 & Web UI (ROSMASTER-X3Plus)

Este paquete ROS centraliza todos los scripts, launch files, backend y frontend web para integrar el modelo local **Llama 3.2 3B** y **YOLO** con el control de movimiento del robot ROSMASTER-X3Plus.

---

## 🛠️ Arquitectura del Sistema

El flujo de control se distribuye entre la **Raspberry Pi (RPi)**, la **Jetson Nano (8GB)** y el **Frontend Web**:

```text
                                  +-----------------------+
                                  |     INTERFAZ WEB      |
                                  |  (index.html + JS)    |
                                  +-----------+-----------+
                                              |
                          WebSocket (9090)    |   HTTP POST (5000)
                    +-------------------------+-------------------------+
                    |                                                   |
                    v                                                   v
      +-------------+-------------+                       +-------------+-------------+
      |                                           |                       |     JETSON NANO 8GB       |
      |                           |                       |                           |
      | - Rosbridge (9090)        |                       | - Ollama (localhost:11434)|
      | - Web Video Server (8080) |                       |   (Llama-3.2-3B local)    |
      | - Camera Astra Node       |                       | - vision_pipeline.py      |
      | - llm_bridge_node.py      |                       | - action_parser.py        |
      | - Mcnamu Driver (motores) |                       |                           |
      +---------------------------+                       +---------------------------+
```

### Flujo de Datos en Modo LLM / Autónomo:
1. **RPi (Cámara):** Publica la imagen en `/camera/rgb/image_raw` y el stream MJPEG en el puerto `8080`.
2. **Jetson (Visión):** El nodo `vision_pipeline.py` procesa la imagen usando YOLO y extrae los objetos y posiciones detectadas.
3. **Jetson (Decisión de Movimiento):** El nodo `vision_pipeline.py` evalúa las detecciones de YOLO de manera local y determinista (milisegundos) y genera un JSON con la acción recomendada de forma inmediata.
4. **Jetson (Parser):** El nodo `action_parser.py` valida el JSON de decisión y lo publica como `geometry_msgs/Twist` en `/llm_cmd`.
5. **RPi (Bridge):** El nodo `llm_bridge_node.py` recibe el comando y lo aplica a los motores (`/cmd_vel`) únicamente si el **Modo LLM** está activo.

### Flujo del Chat de Conversación:
1. **Frontend Web:** El usuario escribe una consulta (ej: *"¿Qué ves?"*) en el chat interactivo de la GUI.
2. **Backend Flask:** El servidor Flask recibe el mensaje y realiza una inyección de contexto, uniendo la personalidad del robot y las últimas detecciones de YOLO en un único mensaje `system` de instrucciones.
3. **Jetson (Ollama):** Envía la conversación junto al prompt unificado de sistema al modelo local **Llama 3.2 3B** en Ollama, el cual responde de manera amigable en lenguaje natural.
4. **Respuesta en Interfaz:** La respuesta se visualiza en los subtítulos flotantes de Mochi, manteniendo una separación total con los motores de movimiento físicos.

---

## 📦 Estructura del Paquete

```text
yahboomcar_llm/
├── CMakeLists.txt                  # Configuración de compilación ROS
├── package.xml                      # Dependencias del paquete ROS
├── README.md                        # Esta documentación
├── launch/
│   ├── rosbridge.launch            # Lanza rosbridge + web_video_server
│   ├── jetson_nodes.launch         # Lanza vision_pipeline + action_parser
│   └── robot_full.launch           # Lanza control completo en RPi (Cam + WS + Bridge)
├── scripts/
│   ├── vision_pipeline.py          # Captura imágenes de ROS y consulta a Ollama
│   ├── action_parser.py            # Valida la salida JSON y la mapea a Twist
│   ├── llm_bridge_node.py          # Multiplexor Manual/LLM + Watchdog de 5s
│   └── start_jetson.sh             # Automatiza carga del GGUF y arranque
└── web_ui/
    ├── app.py                      # Backend Flask con historial de chat
    ├── templates/
    │   └── index.html              # Frontend Web del panel
    └── static/
        ├── css/
        │   └── style.css           # Diseño premium con Glassmorphism
        └── js/
            └── app.js              # Conectividad roslibjs y lógica de chat
```

---

## 🚀 Guía de Arranque y Configuración (Todo en Jetson Nano)

Dado que toda la arquitectura (ROS Master, drivers de motores, cámara, Ollama, Flask y nodos de inferencia) se ejecuta de forma unificada en la **Jetson Nano de 8GB**, el arranque es sumamente directo y no requiere configuraciones de red complejas:

### Paso 1: Compilar el Workspace en la Jetson
Navega a tu workspace `yahboomcar_ws` y compila los paquetes:
```bash
cd ~/Desktop/ROSMASTER-X3Plus_ROS1_code/yahboomcar_ws
catkin_make
source devel/setup.bash
```

### Paso 2: Arrancar todo el stack de ROS e Inferencia
Ejecuta el script de inicio unificado. Este script se encargará de levantar Ollama, importar tu modelo local GGUF `Llama-3.2-3B`, y lanzar todos los nodos (cámara Orbbec Astra, rosbridge, motor driver, vision pipeline y watchdog):
```bash
cd ~/Desktop/ROSMASTER-X3Plus_ROS1_code/yahboomcar_ws/src/yahboomcar_llm/scripts
chmod +x start_jetson.sh vision_pipeline.py action_parser.py
./start_jetson.sh
```

### Paso 3: Lanzar el Servidor Web (Flask)
En otra terminal en la Jetson, inicia el servidor Flask para acceder al panel de control interactivo:
```bash
cd ~/Desktop/ROSMASTER-X3Plus_ROS1_code/yahboomcar_ws/src/yahboomcar_llm/web_ui
python3 app.py
```
Abre tu navegador en `http://localhost:5000` (o desde otro dispositivo en la misma red en `http://<IP_DE_LA_JETSON>:5000`).

---

## 🔒 Parámetros de Seguridad e Integración

### Watchdog de Seguridad (RPi)
El nodo `llm_bridge_node.py` implementa un temporizador de seguridad de **5 segundos**. Si el robot se encuentra en **Modo LLM** y no se recibe un comando en `/llm_cmd` durante más de 5 segundos (por ejemplo, si la Jetson se apaga, pierde WiFi o el modelo de IA tarda demasiado), se publica automáticamente un comando de **STOP** para prevenir accidentes.

### Límites de Velocidad (Jetson)
El nodo `action_parser.py` aplica una saturación de velocidades físicas antes de publicar en `/llm_cmd`:
* **Velocidad Lineal Máxima:** $\pm 0.45\text{ m/s}$
* **Velocidad Angular Máxima:** $\pm 1.2\text{ rad/s}$

---

## 💬 Formato de Mensaje JSON de Acción
El modelo Llama 3.2 genera la acción utilizando esta estructura JSON:
```json
{
  "accion": "forward",
  "velocidad_lineal": 0.25,
  "velocidad_angular": 0.0,
  "razon": "No hay obstáculos al centro, avanzando seguro."
}
```
Si la respuesta no cumple con el formato o falla el parseo, se activa el fallback seguro de **STOP** (`velocidad_lineal: 0.0`, `velocidad_angular: 0.0`).

---

## 🎨 Expresiones de la Cara Mochi (OLED Virtual)
La interfaz incluye una pantalla OLED virtual animada por HTML5 Canvas que emula las expresiones del compañero *Dasai Mochi*:
*   **Sleeping:** Ojos cerrados con líneas planas (cuando no hay conexión WebSocket).
*   **Idle:** Ojos normales que parpadean aleatoriamente cada 2 a 6 segundos.
*   **Happy:** Ojos en forma de arco (`^ ^`) al conectarse o al recibir una respuesta exitosa de Llama 3.2.
*   **Thinking:** Ojos en espiral rotando cuando Llama 3.2 está procesando una consulta.
*   **Dizzy:** Ojos en forma de cruz (`X X`) cuando ocurre un error de red o de comunicación.
*   **Movimiento:** Los ojos se desplazan hacia arriba, abajo, izquierda o derecha según la dirección de marcha del robot.
