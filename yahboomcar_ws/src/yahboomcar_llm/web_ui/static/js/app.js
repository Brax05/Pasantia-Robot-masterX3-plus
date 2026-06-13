// Application State
let rpiIp = localStorage.getItem("rpi_ip") || "";
let ros = null;
let cmdVelPub = null;
let modePub = null;
let armPub = null;
let lastLlmResponseText = "";
let commandTimer = null;
let terminalCloseTimer = null;

// Mochi OLED Face State
const mochiCanvas = document.getElementById("mochi-canvas");
const faceModeBadge = document.getElementById("face-mode-badge");
let mochiState = "sleeping"; // Starts sleeping, wakes up on connection
let blinkState = false;
let lastBlinkTime = 0;
let nextBlinkInterval = 3000;
let eyeAngle = 0; // for spinning thinking eyes

// ROS Topics Configuration
const MANUAL_TOPIC = "cmd_vel_manual";
const MODE_TOPIC = "llm_mode";

// DOM Elements
const wsIndicator = document.getElementById("ws-indicator");
const wsStatusText = document.getElementById("ws-status-text");
const modeToggle = document.getElementById("mode-toggle"); // Optional toggle
const cameraStream = document.getElementById("camera-stream");
const cameraPlaceholder = document.getElementById("camera-placeholder");

const linearSlider = document.getElementById("linear-slider");
const angularSlider = document.getElementById("angular-slider");
const linearVal = document.getElementById("linear-val");
const angularVal = document.getElementById("angular-val");

const chatMessages = document.getElementById("chat-messages");
const llmSubtitle = document.getElementById("llm-subtitle");
const chatInput = document.getElementById("chat-input");
const btnSend = document.getElementById("btn-send");
const btnClearChat = document.getElementById("btn-clear-chat");
const btnCommandParse = document.getElementById("btn-command-parse");

const configModal = document.getElementById("config-modal");
const ipRpiInput = document.getElementById("ip-rpi");
const btnSaveConfig = document.getElementById("btn-save-config");

// Greet Button & Terminal Elements
const btnGreet = document.getElementById("btn-greet");
const faceContainer = document.getElementById("face-container");
const terminalContent = document.getElementById("terminal-content");

// Update displays for sliders (if they exist)
if (linearSlider && linearVal) {
    linearSlider.addEventListener("input", (e) => {
        linearVal.textContent = e.target.value;
    });
}
if (angularSlider && angularVal) {
    angularSlider.addEventListener("input", (e) => {
        angularVal.textContent = e.target.value;
    });
}

// Setup Connection Modal and Face Animation
initMochiFace();

if (!rpiIp) {
    showConfigModal();
} else {
    connectROS();
}

function showConfigModal() {
    configModal.style.display = "block";
    ipRpiInput.value = rpiIp || window.location.hostname;
}

btnSaveConfig.addEventListener("click", () => {
    const enteredIp = ipRpiInput.value.trim();
    if (enteredIp) {
        localStorage.setItem("rpi_ip", enteredIp);
        rpiIp = enteredIp;
        configModal.style.display = "none";
        connectROS();
    }
});

wsIndicator.addEventListener("click", showConfigModal);

// Mochi Face Expression Setter
function setMochiState(state) {
    mochiState = state;
    if (faceModeBadge) {
        faceModeBadge.textContent = state.toUpperCase();
    }

    // Toggle between custom canvas expressions and the official Rive pixel-art GIF
    const mochiGif = document.getElementById("mochi-gif");
    if (state === "happy") {
        if (mochiCanvas) mochiCanvas.style.display = "none";
        if (mochiGif) mochiGif.style.display = "block";
    } else {
        if (mochiCanvas) mochiCanvas.style.display = "block";
        if (mochiGif) mochiGif.style.display = "none";
    }
}

// Slide-Out Terminal Logger
function updateTerminal(label, text) {
    if (!terminalContent) return;
    const timeStr = new Date().toLocaleTimeString();
    const formatted = `[${timeStr}] [${label}] ${text}\n`;
    terminalContent.innerText = formatted + terminalContent.innerText;
}

let subtitleTimer = null;
function displaySubtitle(text) {
    if (!llmSubtitle) return;
    if (subtitleTimer) clearTimeout(subtitleTimer);
    llmSubtitle.innerHTML = text;
    llmSubtitle.classList.add("visible");
    
    // Auto-hide after 8 seconds
    subtitleTimer = setTimeout(() => {
        llmSubtitle.classList.remove("visible");
    }, 8000);
}

// ROS Connection Management
function connectROS() {
    wsIndicator.className = "indicator disconnected";
    wsStatusText.textContent = "Conectando...";
    setMochiState("thinking");
    console.log(`Connecting to ROS on: ws://${rpiIp}:9090`);

    if (ros) {
        try { ros.close(); } catch(e) {}
    }

    ros = new ROSLIB.Ros({
        url: `ws://${rpiIp}:9090`
    });

    ros.on('connection', () => {
        console.log('Connected to websocket server.');
        wsIndicator.className = "indicator connected";
        wsStatusText.textContent = "Conectado";
        setMochiState("happy");
        playRobotSound("connect");
        updateTerminal("RPi", "Conexión WebSocket establecida.");
        
        setTimeout(() => {
            if (mochiState === "happy") setMochiState("idle");
        }, 2500);
        
        setupRosPublishers();
        startCameraStream();
    });

    ros.on('error', (error) => {
        console.log('Error connecting to websocket server: ', error);
        wsIndicator.className = "indicator disconnected";
        wsStatusText.textContent = "Error";
        setMochiState("dizzy");
        playRobotSound("disconnect");
        updateTerminal("ERROR", "Error de enlace al WebSocket (9090).");
        stopCameraStream();
    });

    ros.on('close', () => {
        console.log('Connection to websocket server closed.');
        wsIndicator.className = "indicator disconnected";
        wsStatusText.textContent = "Desconectado";
        setMochiState("sleeping");
        stopCameraStream();
        // Retry connection after 5 seconds
        setTimeout(connectROS, 5000);
    });
}

function setupRosPublishers() {
    // Publisher for manual steering
    cmdVelPub = new ROSLIB.Topic({
        ros: ros,
        name: MANUAL_TOPIC,
        messageType: 'geometry_msgs/Twist'
    });

    // Publisher for mode toggling (manual vs LLM control)
    modePub = new ROSLIB.Topic({
        ros: ros,
        name: MODE_TOPIC,
        messageType: 'std_msgs/Bool'
    });

    // Publisher for Robotic Arm angles
    armPub = new ROSLIB.Topic({
        ros: ros,
        name: 'TargetAngle',
        messageType: 'yahboomcar_msgs/ArmJoint'
    });

    // Automatically enable LLM mode as active (true) on connection
    if (modePub) {
        const boolMsg = new ROSLIB.Message({
            data: true
        });
        modePub.publish(boolMsg);
        console.log("Auto-publishing mode: LLM (true)");
        updateTerminal("SISTEMA", "Modo operativo: LLM/AUTÓNOMO (Activo)");
    }
    if (modeToggle) {
        modeToggle.disabled = false;
        modeToggle.addEventListener("change", (e) => {
            const active = e.target.checked;
            const boolMsg = new ROSLIB.Message({
                data: active
            });
            if (modePub) {
                modePub.publish(boolMsg);
                console.log(`Publishing mode: ${active ? "LLM" : "Manual"}`);
                updateTerminal("SISTEMA", `Modo operativo: ${active ? "LLM/AUTÓNOMO" : "MANUAL"}`);
                playRobotSound("chirp");
            }
        });
    }
}

// Camera Streaming
function startCameraStream() {
    let streamUrl;
    if (rpiIp === "127.0.0.1" || rpiIp === "localhost" || rpiIp === "") {
        streamUrl = `/api/camera_stream`;
    } else {
        streamUrl = `http://${rpiIp}:8080/stream?topic=/camera/rgb/image_raw`;
    }
    console.log(`Loading stream from: ${streamUrl}`);
    cameraStream.src = streamUrl;
    cameraStream.style.display = "block";
    cameraPlaceholder.style.display = "none";
}

function stopCameraStream() {
    if (rpiIp === "127.0.0.1" || rpiIp === "localhost" || rpiIp === "") {
        // For isolated testing, do not close the stream when ROS is missing
        return;
    }
    cameraStream.src = "";
    cameraStream.style.display = "none";
    cameraPlaceholder.style.display = "flex";
}

cameraStream.onerror = () => {
    console.error("Camera stream error. Loading placeholder.");
    stopCameraStream();
};

// D-Pad Movement publishing on Click-and-Hold
const movements = {
    "btn-up":    { lx: 1,  az: 0,   face: "forward" },
    "btn-down":  { lx: -1, az: 0,   face: "backward" },
    "btn-left":  { lx: 0,  az: 1,   face: "left" },
    "btn-right": { lx: 0,  az: -1,  face: "right" },
    "btn-stop":  { lx: 0,  az: 0,   face: "idle" }
};

Object.keys(movements).forEach(btnId => {
    const btn = document.getElementById(btnId);
    if (!btn) return;

    const startMove = (e) => {
        e.preventDefault();
        if (modeToggle ? modeToggle.checked : true) {
            console.log("Ignore manual inputs: LLM mode is active");
            return;
        }
        const m = movements[btnId];
        const linSpeed = (linearSlider ? parseFloat(linearSlider.value) : 0.2) * m.lx;
        const angSpeed = (angularSlider ? parseFloat(angularSlider.value) : 0.5) * m.az;
        setMochiState(m.face);
        publishTwist(linSpeed, angSpeed);
    };

    const stopMove = (e) => {
        e.preventDefault();
        if (modeToggle ? modeToggle.checked : true) return;
        setMochiState("idle");
        publishTwist(0.0, 0.0);
    };

    // Desktop
    btn.addEventListener("mousedown", startMove);
    btn.addEventListener("mouseup", stopMove);
    btn.addEventListener("mouseleave", stopMove);

    // Mobile
    btn.addEventListener("touchstart", startMove, { passive: false });
    btn.addEventListener("touchend", stopMove, { passive: false });
});

function publishTwist(linearX, angularZ) {
    if (!cmdVelPub) {
        console.warn("ROS Publisher not ready.");
        return;
    }

    const twist = new ROSLIB.Message({
        linear: { x: linearX, y: 0.0, z: 0.0 },
        angular: { x: 0.0, y: 0.0, z: angularZ }
    });
    cmdVelPub.publish(twist);
}

// Conversational Chat Interface
btnSend.addEventListener("click", sendChatMessage);
chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendChatMessage();
});

async function sendChatMessage() {
    const prompt = chatInput.value.trim();
    if (!prompt) return;

    // Expand Face card to show explanation terminal
    if (terminalCloseTimer) clearTimeout(terminalCloseTimer);

    // Add user message to UI
    appendBubble("user", prompt);
    chatInput.value = "";
    btnSend.disabled = true;
    setMochiState("thinking");
    playRobotSound("thinking");

    updateTerminal("CONSULTA", `Enviando prompt: "${prompt}"`);
    updateTerminal("LLAMA3.2", "Conectando al LLM local en la Jetson...");

    // Scroll to bottom
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Show typing/loading bubble
    const loadingBubble = appendBubble("robot", `<i class="fa-solid fa-ellipsis fa-bounce"></i> Thinking...`);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });
        
        const data = await response.json();
        
        // Remove typing bubble
        loadingBubble.remove();
        btnSend.disabled = false;

        if (response.ok) {
            lastLlmResponseText = data.respuesta;
            appendBubble("robot", lastLlmResponseText);
            setMochiState("happy");
            playRobotSound("connect");

            updateTerminal("RESPUESTA", "Procesado con éxito.");
            updateTerminal("EXPLICACION", lastLlmResponseText);

            setTimeout(() => {
                if (mochiState === "happy") setMochiState("idle");
            }, 3000);
        } else {
            appendBubble("robot", `Error: ${data.error || "Ocurrió un problema en el backend"}`);
            setMochiState("dizzy");
            updateTerminal("ERROR", `Servidor retornó error: ${data.error}`);
            setTimeout(() => {
                if (mochiState === "dizzy") setMochiState("idle");
            }, 3000);
        }
    } catch(err) {
        loadingBubble.remove();
        btnSend.disabled = false;
        appendBubble("robot", `Error de red: No se pudo contactar al servidor Flask.`);
        setMochiState("dizzy");
        updateTerminal("RED", "Error al conectar con Flask backend (app.py).");
        setTimeout(() => {
            if (mochiState === "dizzy") setMochiState("idle");
        }, 3000);
        console.error("Chat error: ", err);
    }
    
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Auto collapse terminal after 12 seconds
    terminalCloseTimer = setTimeout(() => {
        // Shifting disabled
    }, 12000);
}

btnClearChat.addEventListener("click", async () => {
    if (confirm("¿Seguro que deseas reiniciar el historial del chat?")) {
        try {
            const res = await fetch('/api/chat/reset', { method: 'POST' });
            if (res.ok) {
                if (chatMessages) chatMessages.innerHTML = "";
                appendBubble("robot", "Historial de chat reiniciado. ¿En qué te puedo ayudar hoy?");
                if (btnCommandParse) {
                    btnCommandParse.classList.add("disabled");
                    btnCommandParse.disabled = true;
                }
                lastLlmResponseText = "";
                setMochiState("happy");
                updateTerminal("RESET", "Historial de chat borrado.");
                setTimeout(() => {
                    if (mochiState === "happy") setMochiState("idle");
                }, 2000);
            }
        } catch(e) {
            console.error("Error resetting chat:", e);
        }
    }
});

// Parse Assistant Chat Response to Movement
function executeLlmMovementCommand(responseText) {
    if (!responseText) return;
    
    const text = responseText.toLowerCase();
    let lx = 0.0;
    let az = 0.0;
    let actionName = "";
    let faceState = "idle";

    const linSpeed = linearSlider ? parseFloat(linearSlider.value) : 0.2;
    const angSpeed = angularSlider ? parseFloat(angularSlider.value) : 0.5;

    if (text.includes("adelante") || text.includes("avanza") || text.includes("avanzar")) {
        lx = linSpeed;
        actionName = "Adelante";
        faceState = "forward";
    } else if (text.includes("atrás") || text.includes("retrocede") || text.includes("retroceder") || text.includes("reversa")) {
        lx = -linSpeed;
        actionName = "Atrás";
        faceState = "backward";
    } else if (text.includes("izquierda") || text.includes("gira a la izquierda")) {
        az = angSpeed;
        actionName = "Girar a la Izquierda";
        faceState = "left";
    } else if (text.includes("derecha") || text.includes("gira a la derecha")) {
        az = -angSpeed;
        actionName = "Girar a la Derecha";
        faceState = "right";
    } else if (text.includes("parar") || text.includes("detener") || text.includes("stop")) {
        lx = 0.0;
        az = 0.0;
        actionName = "Detener";
        faceState = "idle";
    }

    if (actionName) {
        appendBubble("robot", `🤖 <strong>Ejecutando comando: ${actionName}</strong> por 1.5 segundos.`);
        if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
        
        updateTerminal("MOTOR", `Ejecutando comando conversacional: ${actionName}`);
        
        // Execute movement & Face expression
        setMochiState(faceState);
        publishTwist(lx, az);

        // Cancel previous timer if any
        if (commandTimer) clearTimeout(commandTimer);

        // Stop after 1.5s
        commandTimer = setTimeout(() => {
            publishTwist(0.0, 0.0);
            setMochiState("happy");
            appendBubble("robot", `🤖 Comando completado. Robot detenido.`);
            updateTerminal("MOTOR", "Comando finalizado. Robot detenido.");
            if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
            
            setTimeout(() => {
                if (mochiState === "happy") setMochiState("idle");
            }, 2000);
        }, 1500);
    }
}

if (btnCommandParse) {
    btnCommandParse.addEventListener("click", () => {
        executeLlmMovementCommand(lastLlmResponseText);
    });
}

// Greet Wave Arm Command sequence
if (btnGreet) {
    btnGreet.addEventListener("click", () => {
        if (!armPub) {
            alert("No hay conexión con ROS. Primero establece la dirección IP en el panel.");
            return;
        }

        console.log("Publishing waving sequence to TargetAngle...");
        setMochiState("happy");
        updateTerminal("BRAZO", "[INICIO] Secuencia de saludo...");
        playRobotSound("chirp");

        // 1. Lift arm and open claw
        publishArm([90.0, 90.0, 90.0, 90.0, 90.0, 150.0], 800);
        
        // 2. Wave Base Left
        setTimeout(() => {
            updateTerminal("BRAZO", "Giro base a la izquierda");
            publishArm([60.0, 90.0, 90.0, 90.0, 90.0, 150.0], 500);
            playRobotSound("chirp");
        }, 800);

        // 3. Wave Base Right
        setTimeout(() => {
            updateTerminal("BRAZO", "Giro base a la derecha");
            publishArm([120.0, 90.0, 90.0, 90.0, 90.0, 150.0], 500);
            playRobotSound("chirp");
        }, 1300);

        // 4. Wave Base Left
        setTimeout(() => {
            updateTerminal("BRAZO", "Giro base a la izquierda");
            publishArm([60.0, 90.0, 90.0, 90.0, 90.0, 150.0], 500);
            playRobotSound("chirp");
        }, 1800);

        // 5. Rest / Home Position
        setTimeout(() => {
            updateTerminal("BRAZO", "Regresando a posición de reposo.");
            publishArm([90.0, 145.0, 0.0, 0.0, 90.0, 31.0], 800);
        }, 2300);

        // 6. Reset Face & slide back terminal
        setTimeout(() => {
            setMochiState("idle");
            updateTerminal("SISTEMA", "Secuencia de saludo finalizada.");
        }, 3100);
    });
}

function publishArm(joints, runTime) {
    if (!armPub) return;
    const msg = new ROSLIB.Message({
        id: 0,
        run_time: runTime,
        angle: 0.0,
        joints: joints
    });
    armPub.publish(msg);
}

// Browser Audio Synthesizer (Web Audio API)
function playRobotSound(type) {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const audioCtx = new AudioContext();

        if (type === "connect") {
            // Rising chime
            playNote(audioCtx, 523.25, 0.08, 0.0); // C5
            playNote(audioCtx, 659.25, 0.12, 0.08); // E5
            playNote(audioCtx, 783.99, 0.16, 0.16); // G5
        } else if (type === "disconnect") {
            // Falling chime
            playNote(audioCtx, 392.00, 0.12, 0.0); // G4
            playNote(audioCtx, 261.63, 0.22, 0.12); // C4
        } else if (type === "chirp") {
            // Retro beep
            playNote(audioCtx, 880.00, 0.04, 0.0); // A5
            playNote(audioCtx, 1046.50, 0.04, 0.04); // C6
        } else if (type === "thinking") {
            // Repeating low pulses
            playNote(audioCtx, 293.66, 0.08, 0.0); // D4
            playNote(audioCtx, 349.23, 0.08, 0.15); // F4
        }
    } catch (e) {
        console.warn("Audio Context blocked or not supported: ", e);
    }
}

function playNote(ctx, freq, duration, delay) {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = "sine";
    osc.frequency.value = freq;
    
    gain.gain.setValueAtTime(0.12, ctx.currentTime + delay);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + duration);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start(ctx.currentTime + delay);
    osc.stop(ctx.currentTime + delay + duration);
}

function appendBubble(role, content) {
    // If we are in the clean fullscreen layout (no chat container), use subtitle overlay for robot
    if (!chatMessages) {
        if (role === "robot") {
            // Strip HTML tags if any (like strong tags in executing commands)
            const cleanContent = content.replace(/<\/?[^>]+(>|$)/g, "");
            displaySubtitle(cleanContent);
        }
        return { remove: () => {} }; // Return dummy object to avoid crash on loadingBubble.remove()
    }
    
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;
    
    const icon = role === "robot" ? "fa-robot" : "fa-user";
    
    msgDiv.innerHTML = `
        <div class="avatar"><i class="fa-solid ${icon}"></i></div>
        <div class="bubble">${content}</div>
    `;
    
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgDiv;
}

// Mochi Canvas Face Drawer
function initMochiFace() {
    if (!mochiCanvas) return;
    const ctx = mochiCanvas.getContext("2d");

    function drawEye(x, y, sizeX, sizeY, eyeType) {
        ctx.fillStyle = "#00f0ff";
        ctx.strokeStyle = "#00f0ff";
        ctx.lineWidth = 6;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.shadowBlur = 12;
        ctx.shadowColor = "rgba(0, 240, 255, 0.6)";

        if (blinkState && eyeType !== "sleeping") {
            // Draw closed eye (blink line)
            ctx.beginPath();
            ctx.moveTo(x - sizeX, y);
            ctx.lineTo(x + sizeX, y);
            ctx.stroke();
            ctx.shadowBlur = 0;
            return;
        }

        switch (eyeType) {
            case "happy":
                // Draw arch '^'
                ctx.beginPath();
                ctx.arc(x, y + 8, sizeX, Math.PI, 0, false);
                ctx.stroke();
                break;
                
            case "dizzy":
                // Draw 'X'
                ctx.beginPath();
                ctx.moveTo(x - sizeX * 0.7, y - sizeY * 0.4);
                ctx.lineTo(x + sizeX * 0.7, y + sizeY * 0.4);
                ctx.moveTo(x + sizeX * 0.7, y - sizeY * 0.4);
                ctx.lineTo(x - sizeX * 0.7, y + sizeY * 0.4);
                ctx.stroke();
                break;
                
            case "thinking":
                // Draw swirling circle segments
                ctx.save();
                ctx.translate(x, y);
                ctx.rotate(eyeAngle);
                ctx.beginPath();
                ctx.arc(0, 0, sizeX * 0.8, 0, Math.PI * 1.5, false);
                ctx.stroke();
                ctx.restore();
                break;

            case "sleeping":
                // Flat line '-'
                ctx.beginPath();
                ctx.moveTo(x - sizeX, y + 5);
                ctx.lineTo(x + sizeX, y + 5);
                ctx.stroke();
                break;

            case "forward":
                // Shift capsule slightly up
                drawCapsule(x, y - 8, sizeX, sizeY);
                break;

            case "backward":
                // Shift capsule slightly down
                drawCapsule(x, y + 8, sizeX, sizeY);
                break;

            case "left":
                // Shift capsule left
                drawCapsule(x - 8, y, sizeX, sizeY);
                break;

            case "right":
                // Shift capsule right
                drawCapsule(x + 8, y, sizeX, sizeY);
                break;

            case "idle":
            default:
                // Regular vertical capsule
                drawCapsule(x, y, sizeX, sizeY);
                break;
        }
        ctx.shadowBlur = 0;
    }

    function drawCapsule(x, y, w, h) {
        ctx.beginPath();
        ctx.arc(x, y - h/2 + w, w, Math.PI, 0, false);
        ctx.lineTo(x + w, y + h/2 - w);
        ctx.arc(x, y + h/2 - w, w, 0, Math.PI, false);
        ctx.lineTo(x - w, y - h/2 + w);
        ctx.closePath();
        ctx.fill();
    }

    function animate(timestamp) {
        ctx.clearRect(0, 0, mochiCanvas.width, mochiCanvas.height);

        // Blinking cycle logic
        if (timestamp - lastBlinkTime > nextBlinkInterval) {
            blinkState = true;
            lastBlinkTime = timestamp;
            nextBlinkInterval = 2500 + Math.random() * 4000;
            // play chirp sound randomly when blinking to sound "alive"
            if (mochiState === "idle" && Math.random() < 0.2) {
                playRobotSound("chirp");
            }
            setTimeout(() => {
                blinkState = false;
            }, 150);
        }

        // Spin swirl eyes for thinking/loading
        if (mochiState === "thinking") {
            eyeAngle += 0.08;
        }

        // Draw left and right eyes
        drawEye(60, 60, 13, 30, mochiState);
        drawEye(140, 60, 13, 30, mochiState);

        requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
}
