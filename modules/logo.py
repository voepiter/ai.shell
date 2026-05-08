# ASCII logo display with lolcat-style rainbow animation
import random
import time
from pathlib import Path

_RESET = "\033[0m"


def _rgb(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _hue_to_rgb(hue: float):
    h = (hue % 1.0) * 6
    i = int(h)
    f = h - i
    if   i == 0: return 1,   f,   0
    elif i == 1: return 1-f, 1,   0
    elif i == 2: return 0,   1,   f
    elif i == 3: return 0,   1-f, 1
    elif i == 4: return f,   0,   1
    else:        return 1,   0,   1-f


def _colorize(line: str, hue_start: float, col_freq: float) -> str:
    parts = []
    for col, ch in enumerate(line):
        r, g, b = _hue_to_rgb(hue_start + col * col_freq)
        parts.append(f"{_rgb(int(r*255), int(g*255), int(b*255))}{ch}")
    parts.append(_RESET)
    return "".join(parts)


def print_logo(path: Path | str, delay: float = 0.05, logo_gradient: float = 0.08):
    p = Path(path)
    if not p.exists():
        return
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return
    max_width = max((len(l) for l in lines), default=1)
    col_freq  = logo_gradient / max_width
    row_freq  = logo_gradient / max(len(lines), 1) * 0.4
    hue_start = random.random()
    print()
    for row, line in enumerate(lines):
        print(_colorize(line, hue_start + row * row_freq, col_freq))
        if delay > 0:
            time.sleep(delay)
    print()
