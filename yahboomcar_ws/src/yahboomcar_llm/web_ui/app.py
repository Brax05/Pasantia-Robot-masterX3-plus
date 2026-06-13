#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import requests
import base64
import time
from flask import Flask, render_template, request, jsonify, Response

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FlaskBackend")

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# Configuration defaults
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.environ.get("OLLAMA_PORT", "11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

if "0.0.0.0" in OLLAMA_HOST:
    OLLAMA_HOST = OLLAMA_HOST.replace("0.0.0.0", "127.0.0.1")

if ":" in OLLAMA_HOST:
    if OLLAMA_HOST.startswith("http://") or OLLAMA_HOST.startswith("https://"):
        OLLAMA_URL = "{}/api/chat".format(OLLAMA_HOST)
    else:
        OLLAMA_URL = "http://{}/api/chat".format(OLLAMA_HOST)
else:
    OLLAMA_URL = "http://{}:{}/api/chat".format(OLLAMA_HOST, OLLAMA_PORT)

# Global variables for isolated local mockup vision pipeline
latest_detections = []
latest_frame = None

# Conversation history in memory
chat_history = [
    {
        "role": "system",
        "content": (
            "Eres el asistente conversacional de un robot móvil ROSMASTER-X3Plus. "
            "Responde en español de forma breve, concisa, útil y amigable. "
            "Si te piden moverte o realizar acciones físicas, puedes sugerir "
            "los comandos correspondientes. Por ejemplo: 'Entendido, me moveré hacia adelante'."
        )
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/vision/update', methods=['POST'])
def vision_update():
    global latest_detections, latest_frame
    data = request.json or {}
    latest_detections = data.get("detections", [])
    logger.info("Received vision update detections: %s", latest_detections)
    frame_b64 = data.get("frame", "")
    if frame_b64:
        try:
            latest_frame = base64.b64decode(frame_b64)
        except Exception as e:
            logger.error("Error decoding base64 frame: %s", str(e))
    return jsonify({"status": "success"})

def gen_mjpeg_frames():
    global latest_frame
    last_sent_frame = None
    while True:
        if latest_frame is not None and latest_frame != last_sent_frame:
            last_sent_frame = latest_frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
        time.sleep(0.1)

@app.route('/api/camera_stream')
def camera_stream():
    return Response(gen_mjpeg_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/chat', methods=['POST'])
def chat():
    global chat_history, latest_detections
    data = request.json or {}
    user_prompt = data.get("prompt", "")

    if not user_prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    # Append user message to history
    chat_history.append({"role": "user", "content": user_prompt})

    # Prepare chat history with visual context injected
    if latest_detections:
        bullet_list = ", ".join(
            "{} en posición {}".format(d['objeto'], d['posicion'])
            for d in latest_detections
        )
        visual_context = (
            "En este momento, tu cámara web está detectando los siguientes objetos en tiempo real: {}. "
            "Ten esto en cuenta en tu respuesta si te preguntan qué ves o si te piden realizar acciones."
        ).format(bullet_list)
    else:
        visual_context = "Tu cámara no detecta ningún objeto u obstáculo en este momento (el camino está despejado)."

    # Merge main system prompt and the current visual context into a single system message
    system_content = (
        "Eres el asistente conversacional de un robot móvil ROSMASTER-X3Plus. "
        "Responde en español de forma breve, concisa, útil y amigable. "
        "Si te piden moverte o realizar acciones físicas, puedes sugerir "
        "los comandos correspondientes. Por ejemplo: 'Entendido, me moveré hacia adelante'."
    )
    system_content += "\n\n[INFORMACIÓN DE LA CÁMARA EN TIEMPO REAL]\n" + visual_context

    messages_with_context = [
        {"role": "system", "content": system_content}
    ]
    for msg in chat_history:
        if msg["role"] != "system":
            messages_with_context.append(msg)

    # Prepare request to Ollama
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages_with_context,
        "stream": False
    }

    try:
        logger.info("Sending chat request to Ollama: %s", OLLAMA_URL)
        logger.info("Full messages payload: %s", messages_with_context)
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        assistant_message = result.get("message", {}).get("content", "")
        logger.info("Ollama response content: %s", assistant_message)
        
        # Append assistant response to history
        chat_history.append({"role": "assistant", "content": assistant_message})
        
        return jsonify({
            "respuesta": assistant_message,
            "historial_len": len(chat_history)
        })

    except requests.RequestException as e:
        logger.error("Error communicating with Ollama: %s", str(e))
        # Remove the user message from history on error to prevent desync
        chat_history.pop()
        return jsonify({
            "error": "Error al comunicarse con el modelo de lenguaje (Ollama)",
            "detalle": str(e)
        }), 500

@app.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    global chat_history, latest_detections
    chat_history = [chat_history[0]]  # Reset and keep only system instructions
    latest_detections = []
    return jsonify({"status": "success", "message": "Historial de chat reiniciado"})

if __name__ == '__main__':
    port = int(os.environ.get("FLASK_PORT", 5000))
    # Run server on all interfaces
    app.run(host='0.0.0.0', port=port, debug=False)
