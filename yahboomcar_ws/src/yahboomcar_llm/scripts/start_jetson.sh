#!/bin/bash

# Configuration
GGUF_DIR="../../Llama-3.2-3B-Instruct-bnb-4bit-gguf"
MODEL_FILE="Llama-3.2-3B-Instruct.F16.gguf"
MODEL_NAME="llama3.2-instruct"
MODELFILE_PATH="Modelfile"

echo "=== Jetson LLM Startup Script ==="

# 1. Start Ollama service if not already running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama server in background..."
    ollama serve &
    sleep 3
else
    echo "Ollama server is already running."
fi

# 2. Check if local GGUF file exists
GGUF_PATH="$GGUF_DIR/$MODEL_FILE"
if [ ! -f "$GGUF_PATH" ]; then
    # Try resolving relative to the script location
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    GGUF_PATH="$SCRIPT_DIR/../../Llama-3.2-3B-Instruct-bnb-4bit-gguf/$MODEL_FILE"
fi

if [ -f "$GGUF_PATH" ]; then
    echo "Found local GGUF model: $GGUF_PATH"
    
    # Check if the model is already registered in Ollama
    if ! ollama list | grep -q "$MODEL_NAME"; then
        echo "Creating Ollama model '$MODEL_NAME' from GGUF..."
        
        # Write Modelfile on the fly
        echo "FROM $GGUF_PATH" > "$MODELFILE_PATH"
        
        # Build model in Ollama
        ollama create "$MODEL_NAME" -f "$MODELFILE_PATH"
        
        # Clean up Modelfile
        rm "$MODELFILE_PATH"
        echo "Model '$MODEL_NAME' successfully registered."
    else
        echo "Model '$MODEL_NAME' is already registered in Ollama."
    fi
else
    echo "[WARNING] Local GGUF file not found at path: $GGUF_PATH"
    echo "Please ensure the path to Llama-3.2-3B-Instruct.F16.gguf is correct."
    echo "Attempting to pull model 'llama3.2:3b' from Ollama registry as fallback..."
    ollama pull llama3.2:3b
    MODEL_NAME="llama3.2:3b"
fi

# 3. Source ROS workspace (adjust path if needed)
if [ -f "/opt/ros/noetic/setup.bash" ]; then
    source /opt/ros/noetic/setup.bash
fi

# Locate workspace root and source devel/setup.bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -f "$WS_DIR/devel/setup.bash" ]; then
    source "$WS_DIR/devel/setup.bash"
    echo "Sourced workspace setup: $WS_DIR/devel/setup.bash"
else
    echo "[WARNING] Could not find workspace setup.bash. Make sure to compile (catkin_make) first."
fi

# 4. Run ROS Nodes
echo "Launching ROS Core, Astra Camera, Rosbridge, and LLM nodes on the Jetson Nano..."
roslaunch yahboomcar_llm robot_full.launch ollama_model:="$MODEL_NAME"
