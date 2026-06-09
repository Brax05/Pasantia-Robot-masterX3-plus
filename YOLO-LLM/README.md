# YOLO + LLM

Proyecto para integrar detección de objetos con YOLO y un modelo LLM local usando Ollama.

## Arquitectura de las carpetas

```text
.
├── .venv/
├── llama_test.py
├── requirements.txt
├── yolo_llm.py
├── yolo_only.py
└── yolo11n.pt
```

## Archivos

- `llama_test.py`: prueba simple de `llama3.2:3b` con la librería `ollama`.
- `yolo_only.py`: detección con webcam usando Ultralytics YOLO.
- `yolo_llm.py`: integra YOLO con Ollama por API local.
- `requirements.txt`: dependencias Python.

## Instalación

1. Ve a la carpeta donde están todos los archivos.
2. Crea el entorno virtual:
   ```powershell
   python -m venv .venv
   ```
3. Activa el entorno:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
4. Instala las dependencias:
   ```powershell
   python -m pip install -r requirements.txt
   ```

## Modelo LLM

Instala el modelo desde otra PowerShell:

```powershell
ollama pull llama3.2:3b
```

## Pruebas

Todas las pruebas se hacen dentro del entorno virtual, después de ejecutar:

```powershell
.venv\Scripts\Activate.ps1
```

### 1. Probar el LLM

```powershell
python llama_test.py
```

### 2. Probar YOLO

```powershell
python yolo_only.py
```

### 3. Probar integración completa

Asegúrate de que Ollama esté ejecutándose:

```powershell
ollama serve
python yolo_llm.py
```

## Notas

- Para salir de las ventanas de OpenCV usa `q` o `ESC`.
- Si tu cámara no abre, cambia `CAMERA_INDEX = 0` por `1` o `2`.
- Puedes cambiar `MODEL_PATH` por otro `.pt` entrenado por ti.
