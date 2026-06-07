#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║               PERSONAJE ASCII — SISTEMA DE NECESIDADES v1.0                ║
# ╠══════════════════════════════════════════════════════════════════════════════╣
# ║  Estructura de carpetas:                                                     ║
# ║    Robot-Fablab\                                                             ║
# ║      Pestañar\   -> Animation_1.txt  Animation2.txt                         ║
# ║                     Animation3.txt  Animation4.txt                          ║
# ║      Saludar\    -> Saludo_1.txt  Saludo_2.txt  Saludo_3.txt                ║
# ║                     Saludo_4.txt  Saludo_5.txt                              ║
# ║      personaje_necesidades.py   <- este script                              ║
# ║                                                                              ║
# ║  Controles:                                                                  ║
# ║    F = Alimentar  |  S = Dormir  |  J = Jugar  |  Q = Salir                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import os, sys, time, shutil, signal, ctypes, random, threading

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — RUTAS DE CARPETAS
# Cada grupo de animaciones vive en su propia subcarpeta.
# Para añadir una animación nueva crea su carpeta aquí y referénciala abajo.
# ══════════════════════════════════════════════════════════════════════════════

ROOT       = r'C:\Users\bprado\Documents\Universidad\Robot-Fablab'

# Carpetas existentes (ya tienes los .txt)
DIR_PESTANAR = os.path.join(ROOT, 'Pestañar')   # Animation_1.txt … Animation4.txt
DIR_SALUDAR  = os.path.join(ROOT, 'Saludar')    # Saludo_1.txt    … Saludo_5.txt

# Carpetas futuras (créalas cuando tengas los .txt listos)
# TODO: crear estas carpetas y añadir los .txt correspondientes
DIR_CANSANCIO  = os.path.join(ROOT, 'Cansancio')   # Cansancio_1.txt  … Cansancio_3.txt
DIR_DORMIDO    = os.path.join(ROOT, 'Dormido')      # Dormido_1.txt    … Dormido_2.txt
DIR_HAMBRIENTO = os.path.join(ROOT, 'Hambriento')   # Hambre_1.txt     … Hambre_3.txt
DIR_TRISTE     = os.path.join(ROOT, 'Triste')       # Triste_1.txt     … Triste_2.txt
DIR_ENFERMO    = os.path.join(ROOT, 'Enfermo')      # Enfermo_1.txt    … Enfermo_3.txt
DIR_FELIZ      = os.path.join(ROOT, 'Feliz')        # Feliz_1.txt      … Feliz_3.txt


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — CONFIGURACIÓN
# Ajusta estos valores para cambiar el ritmo del juego.
# ══════════════════════════════════════════════════════════════════════════════

# Velocidad de decaimiento: puntos que se pierden por segundo
DECAY_HAMBRE    = 1.2
DECAY_ENERGIA   = 0.7
DECAY_FELICIDAD = 0.4

# Cuánto recupera cada acción del usuario
GAIN_COMER  = 35.0
GAIN_DORMIR = 40.0
GAIN_JUGAR  = 25.0

# Umbrales (0–100)
UMBRAL_CRITICO = 25.0   # por debajo → animación urgente
UMBRAL_BAJO    = 50.0   # por debajo → animación de alerta

# Intervalo del tick de necesidades (segundos)
TICK_INTERVALO = 0.5

# Saludo automático: tiempo entre saludos (segundos)
SALUDO_MIN = 15.0
SALUDO_MAX = 40.0

# Tiempos del brazo del saludo (tomados de Saludo_animacion tal cual)
T_SUBE = 0.20
T_BAJA = 0.14


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — CARGADOR DE FRAMES
# Lee un .txt desde una carpeta específica y devuelve (grid, W, H, char).
# ══════════════════════════════════════════════════════════════════════════════

def load_frame(folder, filename, char, required=True):
    """
    Lee 'filename' desde 'folder' y devuelve (grid, W, H, char).
      required=True  → si no existe, imprime error y termina.
      required=False → si no existe, devuelve None (animaciones pendientes).
    """
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        if required:
            print(f"\nERROR: No se encontró '{filename}' en:\n  {folder}")
            sys.exit(1)
        return None

    with open(path, encoding='utf-8', errors='replace') as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    content_rows = [i for i, l in enumerate(lines) if l.strip()]
    if not content_rows:
        return None

    min_r, max_r  = content_rows[0], content_rows[-1]
    cropped       = lines[min_r:max_r + 1]
    content_lines = [l for l in cropped if l.strip()]
    if not content_lines:
        return None

    min_c = min(len(l) - len(l.lstrip()) for l in content_lines)
    max_c = max(len(l.rstrip())           for l in content_lines)
    W, H  = max_c - min_c, len(cropped)

    grid = []
    for l in cropped:
        row = []
        for c in range(min_c, max_c):
            ch = l[c] if c < len(l) else ' '
            row.append(1 if ch.strip() else 0)
        grid.append(row)

    return grid, W, H, char


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — DEFINICIÓN DE ANIMACIONES
# Cada animación indica su carpeta, archivos, secuencia y si es requerida.
# ══════════════════════════════════════════════════════════════════════════════

# ── Animación de espera / parpadeo ────────────────────────────────────────────
# Carpeta: Pestañar\   |   Origen: ojo_animacion.py
OJO_FILES = [
    ('Animation_1.txt', '@'),
    ('Animation2.txt',  '@'),
    ('Animation3.txt',  '@'),
    ('Animation4.txt',  '@'),
]
# Secuencia idéntica a ojo_animacion.py
OJO_SEQUENCE = [
    (0, 2.2),
    (1, 0.07),
    (2, 0.06),
    (3, 0.05),
    (2, 0.06),
    (1, 0.07),
    (0, 0.10),
]

# ── Animación de saludo ───────────────────────────────────────────────────────
# Carpeta: Saludar\   |   Origen: Saludo_animacion
SALUDO_FILES = [
    ('Saludo_1.txt', '@'),   # frame 0 — neutro
    ('Saludo_2.txt', '@'),   # frame 1 — brazo 45°
    ('Saludo_3.txt', '@'),   # frame 2 — brazo 90°
    ('Saludo_4.txt', '@'),   # frame 3 — mano abierta
    ('Saludo_5.txt', '@'),   # frame 4 — brazo bajando 45°
]

# ── Animaciones futuras ───────────────────────────────────────────────────────
# Formato: (id, carpeta, [(archivo, char), ...], [(frame, segundos), ...])
# El sistema las carga solo si TODOS los archivos de la carpeta existen.
# Si faltan, usa el ojo como fallback automáticamente.
#
# PARA AÑADIR UNA NUEVA ANIMACIÓN:
#   1. Crea la carpeta dentro de Robot-Fablab\ (ej: Robot-Fablab\Cansancio\)
#   2. Pon los .txt dentro de esa carpeta
#   3. Añade una entrada aquí con su DIR_, archivos y secuencia
#   4. Ya está — el selector de estado ya tiene la condición preparada
#
ANIMACIONES_FUTURAS = [
    (
        'cansancio', DIR_CANSANCIO,
        [('Cansancio_1.txt','@'), ('Cansancio_2.txt','@'), ('Cansancio_3.txt','@')],
        [(0, 0.8), (1, 0.6), (2, 0.4), (1, 0.6)],
    ),
    (
        'dormido', DIR_DORMIDO,
        [('Dormido_1.txt','@'), ('Dormido_2.txt','@')],
        [(0, 1.2), (1, 0.8)],
    ),
    (
        'hambriento', DIR_HAMBRIENTO,
        [('Hambre_1.txt','@'), ('Hambre_2.txt','@'), ('Hambre_3.txt','@')],
        [(0, 0.5), (1, 0.4), (2, 0.5), (1, 0.4)],
    ),
    (
        'triste', DIR_TRISTE,
        [('Triste_1.txt','@'), ('Triste_2.txt','@')],
        [(0, 1.5), (1, 1.0)],
    ),
    (
        'enfermo', DIR_ENFERMO,
        [('Enfermo_1.txt','@'), ('Enfermo_2.txt','@'), ('Enfermo_3.txt','@')],
        [(0, 0.7), (1, 0.5), (2, 0.4), (1, 0.5)],
    ),
    (
        'feliz', DIR_FELIZ,
        [('Feliz_1.txt','@'), ('Feliz_2.txt','@'), ('Feliz_3.txt','@')],
        [(0, 0.3), (1, 0.3), (2, 0.3), (1, 0.3)],
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — CARGA INICIAL
# ══════════════════════════════════════════════════════════════════════════════

print("Cargando animación de espera (Pestañar)... ", end='', flush=True)
OJO_FRAMES = [load_frame(DIR_PESTANAR, fn, ch, required=True)
              for fn, ch in OJO_FILES]
print("OK")

print("Cargando animación de saludo  (Saludar)... ", end='', flush=True)
SALUDO_FRAMES = [load_frame(DIR_SALUDAR, fn, ch, required=True)
                 for fn, ch in SALUDO_FILES]
print("OK")

# Cargar animaciones futuras (solo si la carpeta y archivos existen)
FRAMES_EXTRA   = {}   # { id: [frame_data, ...] }
SEQUENCE_EXTRA = {}   # { id: [(frame_idx, segundos), ...] }

print("Buscando animaciones opcionales...")
for anim_id, carpeta, archivos, secuencia in ANIMACIONES_FUTURAS:
    frames = []
    ok     = True
    for fn, ch in archivos:
        f = load_frame(carpeta, fn, ch, required=False)
        if f is None:
            ok = False
            break
        frames.append(f)
    if ok:
        FRAMES_EXTRA[anim_id]   = frames
        SEQUENCE_EXTRA[anim_id] = secuencia
        print(f"  [CARGADA]   {anim_id:12s} ← {carpeta}")
    else:
        print(f"  [PENDIENTE] {anim_id:12s} ← {carpeta}  (falta la carpeta o los .txt)")

time.sleep(0.6)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — RENDERIZADOR
# Código idéntico al de ambos scripts originales, parametrizado por lista.
# ══════════════════════════════════════════════════════════════════════════════

def render_frame(frames_list, idx, tw, th):
    grid, W, H, char = frames_list[idx]
    if not grid or W == 0 or H == 0:
        return [' ' * tw] * (th - 1)

    max_cols, max_rows = tw, th - 1

    new_cols = max_cols
    new_rows = int(new_cols * H / W * 0.5)
    if new_rows > max_rows:
        new_rows = max_rows
        new_cols = int(new_rows * W / H * 2.0)
        if new_cols > max_cols:
            new_cols = max_cols
            new_rows = int(new_cols * H / W * 0.5)

    new_cols = max(1, min(new_cols, tw))
    new_rows = max(1, min(new_rows, max_rows))

    pad_l = (tw - new_cols) // 2
    pad_t = (max_rows - new_rows) // 2

    blank = ' ' * tw
    out   = [blank] * pad_t

    for row in range(new_rows):
        sr  = min(int(row * H / new_rows), H - 1)
        buf = [' '] * tw
        for col in range(new_cols):
            sc   = min(int(col * W / new_cols), W - 1)
            hits = 0
            for dr in range(2):
                for dc in range(2):
                    rr = min(sr + dr, H - 1)
                    cc = min(sc + dc, W - 1)
                    hits += grid[rr][cc]
            buf[pad_l + col] = char if hits >= 2 else ' '
        out.append(''.join(buf))

    while len(out) < max_rows:
        out.append(blank)

    return out


_render_cache = {}
_cached_size  = (0, 0)

def get_rendered(anim_id, frame_idx):
    global _render_cache, _cached_size
    tw, th = shutil.get_terminal_size(fallback=(120, 40))
    if (tw, th) != _cached_size:
        _render_cache = {}
        _cached_size  = (tw, th)
    key = (anim_id, frame_idx)
    if key not in _render_cache:
        if anim_id == 'ojo':
            frames_list = OJO_FRAMES
        elif anim_id == 'saludo':
            frames_list = SALUDO_FRAMES
        else:
            frames_list = FRAMES_EXTRA.get(anim_id, OJO_FRAMES)
        idx_safe = min(frame_idx, len(frames_list) - 1)
        _render_cache[key] = render_frame(frames_list, idx_safe, tw, th)
    return _render_cache[key], tw, th


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — API DE TERMINAL (igual en ambos scripts originales)
# ══════════════════════════════════════════════════════════════════════════════

class _COORD(ctypes.Structure):
    _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]

class _CURSOR_INFO(ctypes.Structure):
    _fields_ = [('dwSize', ctypes.c_int), ('bVisible', ctypes.c_int)]

def _handle():
    return ctypes.windll.kernel32.GetStdHandle(-11) if os.name == 'nt' else None

def hide_cursor():
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleCursorInfo(_handle(), ctypes.byref(_CURSOR_INFO(1, 0)))
    else:
        sys.stdout.write('\033[?25l'); sys.stdout.flush()

def show_cursor():
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleCursorInfo(_handle(), ctypes.byref(_CURSOR_INFO(100, 1)))
    else:
        sys.stdout.write('\033[?25h'); sys.stdout.flush()

def goto(x, y):
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleCursorPosition(_handle(), _COORD(x, y))
    else:
        sys.stdout.write(f'\033[{y+1};{x+1}H'); sys.stdout.flush()

def enable_ansi():
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetConsoleMode(_handle(), 0x0001 | 0x0004)
        except Exception:
            pass

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_frame_lines(lines, tw):
    goto(0, 0)
    sys.stdout.write('\r\n'.join(line[:tw] for line in lines))
    sys.stdout.flush()


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — SISTEMA DE NECESIDADES
# ══════════════════════════════════════════════════════════════════════════════

class Necesidades:
    def __init__(self):
        self.hambre    = 80.0
        self.energia   = 90.0
        self.felicidad = 75.0
        self.salud     = 100.0
        self._lock     = threading.Lock()
        self._running  = False

    def snapshot(self):
        with self._lock:
            return {
                'hambre':    self.hambre,
                'energia':   self.energia,
                'felicidad': self.felicidad,
                'salud':     self.salud,
            }

    def comer(self):
        with self._lock:
            self.hambre = min(100.0, self.hambre + GAIN_COMER)

    def dormir(self):
        with self._lock:
            self.energia = min(100.0, self.energia + GAIN_DORMIR)

    def jugar(self):
        with self._lock:
            self.felicidad = min(100.0, self.felicidad + GAIN_JUGAR)

    def _tick(self):
        dt = TICK_INTERVALO
        with self._lock:
            # Hambre y energía bajan con el tiempo
            self.hambre  = max(0.0, self.hambre  - DECAY_HAMBRE  * dt)
            self.energia = max(0.0, self.energia - DECAY_ENERGIA * dt)

            # Felicidad sube si todo va bien, baja si algo falla
            if self.hambre >= UMBRAL_BAJO and self.energia >= UMBRAL_BAJO:
                self.felicidad = min(100.0, self.felicidad + 0.3 * dt)
            else:
                self.felicidad = max(0.0, self.felicidad - DECAY_FELICIDAD * dt)

            # Salud se daña si hambre o energía están en zona crítica
            if self.hambre < UMBRAL_CRITICO or self.energia < UMBRAL_CRITICO:
                self.salud = max(0.0, self.salud - 0.3 * dt)
            else:
                self.salud = min(100.0, self.salud + 0.1 * dt)

    def _loop(self):
        while self._running:
            self._tick()
            time.sleep(TICK_INTERVALO)

    def start(self):
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self._running = False


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 9 — SELECTOR DE ESTADO
# Devuelve el id de la animación a reproducir según las necesidades.
# Si la animación aún no está cargada, cae al ojo (fallback automático).
#
# PARA AÑADIR UN NUEVO ESTADO:
#   1. Crea la carpeta y los .txt (Sección 1 y 4)
#   2. Añade un elif aquí con la condición y el id
# ══════════════════════════════════════════════════════════════════════════════

def seleccionar_estado(nec: dict) -> str:
    def lista(anim_id):
        return anim_id in FRAMES_EXTRA

    # Prioridad 1 — Salud crítica
    if nec['salud'] < UMBRAL_CRITICO and lista('enfermo'):
        return 'enfermo'

    # Prioridad 2 — Energía crítica (se duerme)
    if nec['energia'] < UMBRAL_CRITICO and lista('dormido'):
        return 'dormido'

    # Prioridad 3 — Hambre crítica
    if nec['hambre'] < UMBRAL_CRITICO and lista('hambriento'):
        return 'hambriento'

    # Prioridad 4 — Energía baja (cansancio)
    if nec['energia'] < UMBRAL_BAJO and lista('cansancio'):
        return 'cansancio'

    # Prioridad 5 — Felicidad crítica (triste)
    if nec['felicidad'] < UMBRAL_CRITICO and lista('triste'):
        return 'triste'

    # Default — espera con parpadeo
    return 'ojo'


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 10 — HUD (barras de necesidades en las últimas filas)
# ══════════════════════════════════════════════════════════════════════════════

ANSI_ROJO     = '\033[91m'
ANSI_AMARILLO = '\033[93m'
ANSI_VERDE    = '\033[92m'
ANSI_RESET    = '\033[0m'

def _color(v):
    if v < UMBRAL_CRITICO: return ANSI_ROJO
    if v < UMBRAL_BAJO:    return ANSI_AMARILLO
    return ANSI_VERDE

def _barra(v, largo=8):
    n = int(v / 100 * largo)
    return '[' + '█' * n + '░' * (largo - n) + ']'

def draw_hud(nec, tw, th, estado, hint=''):
    goto(0, th - 2)
    hud = (
        f" {_color(nec['hambre'])}Hambre{_barra(nec['hambre'])}{ANSI_RESET}  "
        f"{_color(nec['energia'])}Energia{_barra(nec['energia'])}{ANSI_RESET}  "
        f"{_color(nec['felicidad'])}Felicidad{_barra(nec['felicidad'])}{ANSI_RESET}  "
        f"{_color(nec['salud'])}Salud{_barra(nec['salud'])}{ANSI_RESET}  "
        f"| {estado}"
    )
    sys.stdout.write(hud[:tw])

    goto(0, th - 1)
    ctrl = " [F]Comer  [S]Dormir  [J]Jugar  [Q]Salir"
    if hint:
        ctrl += f"   ← {hint}"
    sys.stdout.write(ctrl[:tw])
    sys.stdout.flush()


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 11 — TECLADO NO BLOQUEANTE
# ══════════════════════════════════════════════════════════════════════════════

if os.name == 'nt':
    import msvcrt
    def poll_key():
        return msvcrt.getwch().lower() if msvcrt.kbhit() else None
else:
    import tty, termios, select
    def poll_key():
        fd  = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            if select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 12 — SALUDO (lógica de Saludo_animacion intacta)
# ══════════════════════════════════════════════════════════════════════════════

def _show_saludo_frame(idx, delay):
    global _cached_size
    tw, th = shutil.get_terminal_size(fallback=(120, 40))
    if (tw, th) != _cached_size:
        clear_screen()
    lines, tw, th = get_rendered('saludo', idx)
    draw_frame_lines(lines, tw)
    time.sleep(delay)

def _hold_waving(seconds):
    """Wave suave mientras el brazo está en alto (de Saludo_animacion)."""
    global _cached_size
    wave_cycle = [(3, 0.35), (2, 0.28), (3, 0.35), (2, 0.25)]
    deadline   = time.monotonic() + seconds
    i          = 0
    while time.monotonic() < deadline:
        fi, delay    = wave_cycle[i % len(wave_cycle)]
        actual_delay = min(delay, deadline - time.monotonic())
        if actual_delay <= 0:
            break
        tw, th = shutil.get_terminal_size(fallback=(120, 40))
        if (tw, th) != _cached_size:
            clear_screen()
        lines, tw, th = get_rendered('saludo', fi)
        draw_frame_lines(lines, tw)
        time.sleep(actual_delay)
        i += 1

def ejecutar_saludo():
    """Secuencia completa de saludo: subida → hold con wave → bajada."""
    hold_t = random.uniform(1.5, 3.5)
    _show_saludo_frame(1, T_SUBE)   # brazo 45°
    _show_saludo_frame(2, T_SUBE)   # brazo 90°
    _show_saludo_frame(3, T_SUBE)   # mano abierta
    _hold_waving(hold_t)
    _show_saludo_frame(2, T_BAJA)   # bajando 90°
    _show_saludo_frame(4, T_BAJA)   # bajando 45°
    _show_saludo_frame(0, T_BAJA)   # neutro


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 13 — MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════════

def on_exit(sig=None, frame=None):
    show_cursor()
    clear_screen()
    print('¡Hasta luego!')
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT,  on_exit)
    signal.signal(signal.SIGTERM, on_exit)

    enable_ansi()
    clear_screen()
    hide_cursor()

    nec = Necesidades()
    nec.start()

    global _cached_size

    proximo_saludo = time.monotonic() + random.uniform(SALUDO_MIN, SALUDO_MAX)
    hint           = ''
    hint_expiry    = 0.0
    estado_actual  = 'ojo'
    anim_step      = 0
    ultimo_frame_t = time.monotonic()

    try:
        while True:
            now      = time.monotonic()
            tw, th   = shutil.get_terminal_size(fallback=(120, 40))
            nec_snap = nec.snapshot()

            # ── Resize ────────────────────────────────────────────────────
            if (tw, th) != _cached_size:
                clear_screen()
                _render_cache.clear()
                _cached_size = (tw, th)

            # ── Teclado ───────────────────────────────────────────────────
            key = poll_key()
            if key in ('q', '\x03'):
                break
            elif key == 'f':
                nec.comer();  hint = '¡Ñam! (+hambre)';    hint_expiry = now + 2.0
            elif key == 's':
                nec.dormir(); hint = 'Zzzz... (+energia)'; hint_expiry = now + 2.0
            elif key == 'j':
                nec.jugar();  hint = '¡Yuhu! (+felicidad)'; hint_expiry = now + 2.0
                # TODO: ejecutar_animacion('feliz') cuando tengas los .txt

            # ── Selector de estado ────────────────────────────────────────
            nuevo_estado = seleccionar_estado(nec_snap)

            # Reiniciar paso si cambia el estado
            if nuevo_estado != estado_actual:
                estado_actual  = nuevo_estado
                anim_step      = 0
                ultimo_frame_t = now

            # ── Saludo automático (solo en estado normal) ─────────────────
            if now >= proximo_saludo and estado_actual == 'ojo':
                ejecutar_saludo()
                proximo_saludo = now + random.uniform(SALUDO_MIN, SALUDO_MAX)
                anim_step      = 0
                ultimo_frame_t = time.monotonic()
                continue

            # ── Reproducir animación activa ───────────────────────────────
            if estado_actual == 'ojo':
                seq = OJO_SEQUENCE
            elif estado_actual in SEQUENCE_EXTRA:
                seq = SEQUENCE_EXTRA[estado_actual]
            else:
                seq = OJO_SEQUENCE   # fallback si la animación no está lista

            fi, dur = seq[anim_step % len(seq)]
            if now - ultimo_frame_t >= dur:
                anim_step     += 1
                ultimo_frame_t = now
                fi, dur        = seq[anim_step % len(seq)]

            lines, tw, th = get_rendered(estado_actual, fi)
            draw_frame_lines(lines, tw)

            # ── HUD ───────────────────────────────────────────────────────
            hint_actual = hint if now < hint_expiry else ''
            draw_hud(nec_snap, tw, th, estado_actual, hint_actual)

            time.sleep(0.02)

    except KeyboardInterrupt:
        pass
    finally:
        nec.stop()
        show_cursor()
        clear_screen()
        print('¡Hasta luego!')

if __name__ == '__main__':
    main()