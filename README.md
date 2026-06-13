# robos_final - Guía de Pruebas Globales (ROSMASTER-X3Plus en Jetson Nano)

Esta carpeta es un repositorio completamente **autónomo y autocontenido** que unifica todo el software del robot ROSMASTER-X3Plus (incluyendo drivers, cámara, modelos de IA y panel web). Está listo para que simplemente lo descargues en tu Jetson Nano (8GB) y arranques las pruebas de inmediato.

---

## 📂 Contenido de la Carpeta Unificada

*   **`Llama-3.2-3B-Instruct-bnb-4bit-gguf/`**: Contiene el modelo local `Llama-3.2-3B-Instruct.F16.gguf` para Ollama.
*   **`yahboomcar_ws/`**: El espacio de trabajo (Workspace) completo de ROS. Contiene:
    *   `src/yahboomcar_llm`: Nuestro paquete de integración (launch files, scripts y la interfaz Web).
    *   `src/yahboomcar_bringup` y `yahboomcar_msgs`: Drivers de motores y mensajes del brazo robótico.
    *   `src/orbbec-ros-sdk`: El driver oficial de la cámara de profundidad Orbbec Astra Pro Plus.
    *   *Todos los demás paquetes originales de movimiento y navegación del robot.*
*   **`py_install/`**: La librería Python `Rosmaster_Lib` para comunicarse con la placa controladora STM32 (copiada como respaldo).

---

## 🛠️ Instalación de Dependencias (En la Jetson Nano)

Asegúrate de instalar los paquetes de ROS necesarios para el WebSocket y streaming de video:
```bash
sudo apt update
sudo apt install ros-noetic-rosbridge-suite ros-noetic-web-video-server
```

Instala las dependencias de Python requeridas utilizando el archivo unificado de requerimientos:
```bash
cd robos_final/yahboomcar_ws/src/yahboomcar_llm
pip install -r requirements.txt
```

---

## 🚀 Guía de Arranque en 3 Pasos (Todo local en Jetson Nano)

### Paso 1: Compilar el Workspace Completo
Dado que todo el código necesario ya está unificado en la carpeta `yahboomcar_ws`, compila directamente aquí:
```bash
cd robos_final/yahboomcar_ws
catkin_make
source devel/setup.bash
```

### Paso 2: Arrancar todo el Robot e Inferencia LLM
Ejecuta el script unificado. Este script levantará Ollama, importará tu modelo local GGUF `Llama-3.2-3B`, y lanzará la cámara, websocket de la interfaz, selector manual/LLM, watchdog de seguridad y nodos de inferencia con una sola instrucción:
```bash
cd src/yahboomcar_llm/scripts
chmod +x start_jetson.sh vision_pipeline.py action_parser.py
./start_jetson.sh
```

### Paso 3: Iniciar el Servidor de la Interfaz Web (Flask)
En otra terminal en la Jetson, arranca la UI web:
```bash
cd robos_final/yahboomcar_ws/src/yahboomcar_llm/web_ui
python3 app.py
```
Abre en tu navegador: `http://localhost:5000` (o `http://<IP_DE_LA_JETSON>:5000` desde otro dispositivo en tu red local).

---

## 📋 Checklist de Pruebas y Verificación

### 1. Prueba de Movimiento Manual y Audio
*   Verifica que al abrir la UI e introducir la IP en la configuración modal, el indicador cambie a **Conectado (Verde)** y la UI emita un sonido alegre de robot.
*   Eleva las ruedas del robot.
*   Presiona los botones del D-Pad (Adelante, Atrás, etc.) y comprueba que las ruedas giran y que la **cara de Mochi desplaza sus ojos** en la dirección pulsada.
*   Suelta el botón y comprueba que el robot se detiene e interactúa parpadeando.

### 2. Prueba del Brazo Robótico (Saludar)
*   Haz clic en el botón **"Saludar con el Brazo"** de la interfaz.
*   El robot levantará el brazo, moverá el servo base de izquierda a derecha 3 veces (saludando), y regresará a la posición de reposo mientras la cara muestra una gran sonrisa pixelada.

### 3. Prueba de Interacción Conversacional (Llama 3.2 3B)
*   Envía una consulta al chat en el panel derecho (ej. *"¿cómo estás?"* o *"gira a la izquierda por favor"*).
*   Comprueba que:
    1.  La cara de Mochi entra en modo **Thinking** (ojos en remolino).
    2.  La tarjeta de la cara se **desplaza a la izquierda**, revelando a la derecha el panel de **"Razonamiento del Robot"** con una terminal cyan que detalla las etapas del procesamiento.
    3.  Una vez completada la respuesta, Mochi muestra la animación pixelada de sonrisa (GIF) y la terminal expone la respuesta detallada.
*   Si la respuesta sugiere un movimiento, haz clic en **"Enviar respuesta como comando"** para que el robot se desplace de forma segura por 1.5 segundos.

### 4. Prueba del Watchdog de Seguridad (Modo LLM)
*   Cambia al interruptor **Modo LLM** en el encabezado de la UI.
*   Apaga forzadamente el nodo de inferencia en la Jetson (presiona `Ctrl + C` en su consola).
*   Comprueba que en un máximo de **5 segundos**, la RPi detecta la pérdida de señal, emite un pitido de advertencia largo a través del buzzer físico, y manda un comando de **STOP** a las ruedas.
