"""Inline /command autocomplete for interactive chat — ghost text + right-arrow accept."""
import os
import sys
import tty
import termios
import select
import readline
from . import colors as _col
from . import skills as _skills

# All built-in slash commands
_BUILTIN = [
    "/quit", "/exit", "/q",
    "/help", "/?",
    "/list-providers", "/lp",
    "/list-models", "/lm",
    "/model",
    "/provider",
    "/shell",
    "/language",
    "/usage", "/u",
    "/clear", "/cls",
    "/verbose",
    "/skill",
    "/sessions",
    "/resume",
    "/changelog",
    "/telegram",
]

_ESC   = "\x1b"
_RIGHT = "\x1b[C"
_LEFT  = "\x1b[D"
_UP    = "\x1b[A"
_DOWN  = "\x1b[B"
_DEL   = "\x1b[3~"


def _all_commands(config_loader) -> list[str]:
    """Return sorted list of all /commands including skill names."""
    cmds = list(_BUILTIN)
    for name, _ in _skills.list_skills(config_loader):
        cmds.append(f"/{name}")
    return sorted(set(cmds))


def _complete(text: str, commands: list[str]) -> str:
    """Return completion suffix if exactly one command starts with text, else ''."""
    if not text.startswith("/"):
        return ""
    matches = [c for c in commands if c.startswith(text) and c != text]
    if len(matches) == 1:
        return matches[0][len(text):]
    return ""


def _read_escape(fd: int) -> str:
    """Read rest of an escape sequence after ESC; return ESC alone if nothing follows in 50 ms."""
    ready, _, _ = select.select([fd], [], [], 0.05)
    if not ready:
        return _ESC
    b = os.read(fd, 1)
    ch = chr(b[0])
    if ch != "[":
        return _ESC + ch
    seq = ch
    while True:
        ready, _, _ = select.select([fd], [], [], 0.05)
        if not ready:
            break
        c = chr(os.read(fd, 1)[0])
        seq += c
        if c.isalpha() or c == "~":
            break
    return _ESC + seq


def read_input(prompt_str: str, config_loader) -> str:
    """Read one line with inline /command ghost text; right-arrow or Tab accept completion."""
    commands = _all_commands(config_loader)

    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)

    buf:      list[str] = []
    pos       = 0         # cursor position in buf
    hist_idx  = -1        # -1 = live input
    saved_buf: list[str] = []

    def _ghost() -> str:
        return _complete("".join(buf) if pos == len(buf) else "", commands)

    def _redraw(ghost: str) -> None:
        text      = "".join(buf)
        ghost_str = f"\x1b[2m{ghost}\x1b[0m" if ghost else ""
        tail_len  = len(buf) - pos
        back_cols = len(ghost) + tail_len
        sys.stdout.write(f"\r{prompt_str}{text}{ghost_str}\x1b[K")
        if back_cols:
            sys.stdout.write(f"\x1b[{back_cols}D")
        sys.stdout.flush()

    sys.stdout.write(prompt_str)
    sys.stdout.flush()

    try:
        tty.setraw(fd)
        while True:
            raw_byte = os.read(fd, 1)
            if not raw_byte:
                break
            ch = chr(raw_byte[0])

            if ch in ("\r", "\n"):  # Enter
                ghost = _ghost()
                sys.stdout.write(f"\x1b[2m{ghost}\x1b[0m\r\n")
                sys.stdout.flush()
                line = "".join(buf)
                if line:
                    readline.add_history(line)
                return line

            elif ch == "\x03":  # Ctrl+C
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                raise KeyboardInterrupt

            elif ch == "\x04":  # Ctrl+D — EOF only on empty line
                if not buf:
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    raise EOFError

            elif ch in ("\x7f", "\x08"):  # Backspace
                if pos > 0:
                    buf.pop(pos - 1)
                    pos -= 1
                    _redraw(_ghost())

            elif ch == "\t":  # Tab — accept ghost if unique match
                ghost = _ghost()
                if ghost and pos == len(buf):
                    buf.extend(ghost)
                    pos = len(buf)
                    _redraw("")

            elif ch == _ESC:  # Escape sequence
                seq = _read_escape(fd)

                if seq == _RIGHT:
                    ghost = _ghost()
                    if ghost and pos == len(buf):
                        buf.extend(ghost)
                        pos = len(buf)
                        _redraw("")
                    elif pos < len(buf):
                        pos += 1
                        _redraw(_ghost())

                elif seq == _LEFT:
                    if pos > 0:
                        pos -= 1
                        _redraw(_ghost())

                elif seq == _UP:  # previous history entry
                    hist_len = readline.get_current_history_length()
                    if hist_idx == -1:
                        saved_buf = list(buf)
                        hist_idx  = hist_len + 1
                    if hist_idx > 1:
                        hist_idx -= 1
                        entry = readline.get_history_item(hist_idx) or ""
                        buf   = list(entry)
                        pos   = len(buf)
                        _redraw("")

                elif seq == _DOWN:  # next history entry
                    if hist_idx != -1:
                        hist_len = readline.get_current_history_length()
                        if hist_idx < hist_len:
                            hist_idx += 1
                            entry = readline.get_history_item(hist_idx) or ""
                            buf   = list(entry)
                            pos   = len(buf)
                        else:
                            hist_idx = -1
                            buf      = list(saved_buf)
                            pos      = len(buf)
                        _redraw(_ghost())

                elif seq == _DEL:  # Delete key
                    if pos < len(buf):
                        buf.pop(pos)
                        _redraw(_ghost())

            elif ch >= " ":  # printable character
                buf.insert(pos, ch)
                pos += 1
                hist_idx = -1
                _redraw(_ghost())

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

    return "".join(buf)
