#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ojo ASCII parpadeando - Windows Terminal
Los archivos deben estar en la misma carpeta que este script:
  Animation_1.txt  Animation2.txt  Animation3.txt  Animation4.txt
Ejecutar:  python ojo_animacion.py
Salir:     Ctrl+C
"""
import os, sys, time, shutil, signal, ctypes

# ── Cargar frames desde los .txt ──────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))

FRAME_FILES = [
    ('Animation_1.txt', '@'),
    ('Animation2.txt',  '@'),
    ('Animation3.txt',  '@'),
    ('Animation4.txt',  '@'),
]

def load_frame(filename, char):
    path = os.path.join(HERE, filename)
    if not os.path.exists(path):
        print(f"ERROR: No se encontro '{filename}' en {HERE}")
        sys.exit(1)
    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    lines = [l.rstrip('\n') for l in lines]
    # encontrar bounding box de contenido
    content_rows = [i for i, l in enumerate(lines) if l.strip()]
    if not content_rows:
        return [], 0, 0, char
    min_r = content_rows[0]
    max_r = content_rows[-1]
    cropped = lines[min_r:max_r + 1]
    content_lines = [l for l in cropped if l.strip()]
    min_c = min(len(l) - len(l.lstrip()) for l in content_lines)
    max_c = max(len(l.rstrip()) for l in content_lines)
    W = max_c - min_c
    H = len(cropped)
    # construir grilla binaria
    grid = []
    for l in cropped:
        row = []
        for c in range(min_c, max_c):
            ch = l[c] if c < len(l) else ' '
            row.append(1 if ch.strip() else 0)
        grid.append(row)
    return grid, W, H, char

print("Cargando frames...", end=' ', flush=True)
FRAMES = [load_frame(fn, ch) for fn, ch in FRAME_FILES]
print("OK")
time.sleep(0.4)

# Secuencia: (indice_frame, segundos)
SEQUENCE = [
    (0, 2.2),
    (1, 0.07),
    (2, 0.06),
    (3, 0.05),
    (2, 0.06),
    (1, 0.07),
    (0, 0.10),
]

# ── Escalado con aspecto correcto ─────────────────────────────────────────────
def render_frame(idx, tw, th):
    grid, W, H, char = FRAMES[idx]
    if not grid or W == 0 or H == 0:
        return [' ' * tw] * (th - 1)

    max_cols = tw
    max_rows = th - 1

    # chars de terminal son ~2x mas altos que anchos en pixels
    # => para preservar aspecto: new_rows = new_cols * (H/W) * 0.5
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
    out = []

    for _ in range(pad_t):
        out.append(blank)

    for row in range(new_rows):
        sr = min(int(row * H / new_rows), H - 1)
        buf = [' '] * tw
        for col in range(new_cols):
            sc = min(int(col * W / new_cols), W - 1)
            # supersampling 2x2
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

# ── Cache ─────────────────────────────────────────────────────────────────────
_render_cache = {}
_cached_size  = (0, 0)

def get_rendered(idx):
    global _render_cache, _cached_size
    tw, th = shutil.get_terminal_size(fallback=(120, 40))
    if (tw, th) != _cached_size:
        _render_cache = {}
        _cached_size  = (tw, th)
    if idx not in _render_cache:
        _render_cache[idx] = render_frame(idx, tw, th)
    return _render_cache[idx], tw, th

# ── Windows API ───────────────────────────────────────────────────────────────
class _COORD(ctypes.Structure):
    _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]

class _CURSOR_INFO(ctypes.Structure):
    _fields_ = [('dwSize', ctypes.c_int), ('bVisible', ctypes.c_int)]

def _handle():
    return ctypes.windll.kernel32.GetStdHandle(-11)

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
        ctypes.windll.kernel32.SetConsoleMode(_handle(), 0x0001 | 0x0004)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ── Dibujar ───────────────────────────────────────────────────────────────────
def draw_frame(lines, tw):
    goto(0, 0)
    # Todo de una sola escritura: sin scroll, sin parpadeo
    out = '\r\n'.join(line[:tw] for line in lines)
    sys.stdout.write(out)
    sys.stdout.flush()

# ── Main ──────────────────────────────────────────────────────────────────────
def on_exit(sig, frame):
    show_cursor()
    clear_screen()
    print('Animacion terminada.')
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT,  on_exit)
    signal.signal(signal.SIGTERM, on_exit)

    enable_ansi()
    clear_screen()
    hide_cursor()

    global _cached_size
    try:
        while True:
            for frame_idx, delay in SEQUENCE:
                tw, th = shutil.get_terminal_size(fallback=(120, 40))
                if (tw, th) != _cached_size:
                    clear_screen()
                lines, tw, th = get_rendered(frame_idx)
                draw_frame(lines, tw)
                time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        clear_screen()
        print('Animacion terminada.')

if __name__ == '__main__':
    main()