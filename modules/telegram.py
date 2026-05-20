"""Telegram bot integration — polling loop and LLM dispatch."""
import getpass
import re
import socket
import sys
import threading
import time
import requests
from . import colors as _col
from . import text as ct
from . import symbols as sym
from . import ui
from . import completer as _completer
from .agent import agentic_loop, build_system_instruction
from .shell import extract_commands
from .spinner import Spinner
from . import skills as _skills
from .locale import t
from providers import APIError

_R    = ct.resetcolor
_BASE = "https://api.telegram.org/bot{token}/{method}"
_lock = threading.Lock()  # serialise LLM calls

_histories: dict[int, list] = {}  # per chat_id conversation history
_instance_id = f"{getpass.getuser()}@{socket.gethostname()}"
_BOT_MSG = re.compile(r'^@\S+:')  # messages from other bot instances


class _CRLFStdout:
    """Wraps sys.stdout to convert \\n → \\r\\n for raw-mode terminal output from background thread."""
    def __init__(self, w):        self._w = w
    def write(self, s: str) -> int: return self._w.write(s.replace("\n", "\r\n"))
    def flush(self):              self._w.flush()
    def __getattr__(self, name):  return getattr(self._w, name)


# ── Telegram API helpers ──────────────────────────────────────────────────

def _api_post(token: str, method: str, **kwargs) -> dict | None:
    """POST to Telegram Bot API; return JSON or None on error."""
    url = _BASE.format(token=token, method=method)
    try:
        r = requests.post(url, json=kwargs, timeout=(5, 30))
        return r.json()
    except KeyboardInterrupt:
        raise
    except requests.exceptions.ConnectionError:
        print(f" {_col.error}telegram: service unavailable{_R}", file=sys.stderr)
        return None
    except requests.exceptions.Timeout:
        print(f" {_col.error}telegram: request timeout{_R}", file=sys.stderr)
        return None
    except Exception as e:
        print(f" {_col.error}telegram: {e}{_R}", file=sys.stderr)
        return None


def _send(token: str, chat_id: int, text: str) -> None:
    """Send HTML message; fall back to plain text on parse error."""
    res = _api_post(token, "sendMessage", chat_id=chat_id,
                    text=text, parse_mode="HTML")
    if res and not res.get("ok"):
        _api_post(token, "sendMessage", chat_id=chat_id, text=text)


def _get_updates(token: str, offset: int) -> list | None:
    """Long-poll getUpdates; return list of updates, [] on soft error, None on ConnectionError."""
    url = _BASE.format(token=token, method="getUpdates")
    try:
        r = requests.get(url, params={"offset": offset, "timeout": 30},
                         timeout=(5, 35))
        d = r.json()
        if not d.get("ok"):
            desc = d.get("description", "unknown error")
            print(f" {_col.error}telegram: {desc}{_R}", file=sys.stderr)
            return []
        return d.get("result", [])
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return []


# ── Markdown → Telegram HTML ──────────────────────────────────────────────

_FENCE  = re.compile(r"```(?:\w+)?\n?(.*?)```",   re.DOTALL)
_ICODE  = re.compile(r"`([^`\n]+)`")
_BOLD   = re.compile(r"\*\*(.+?)\*\*",            re.DOTALL)
_ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)|_([^_\n]+)_")


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(text: str) -> str:
    """Escape HTML and apply bold/italic/inline-code to a plain-text segment."""
    parts, last = [], 0
    for m in _ICODE.finditer(text):
        seg = _esc(text[last:m.start()])
        seg = _BOLD.sub(lambda x: f"<b>{x.group(1)}</b>", seg)
        seg = _ITALIC.sub(lambda x: f"<i>{x.group(1) or x.group(2)}</i>", seg)
        parts.append(seg)
        parts.append(f"<code>{_esc(m.group(1))}</code>")
        last = m.end()
    seg = _esc(text[last:])
    seg = _BOLD.sub(lambda x: f"<b>{x.group(1)}</b>", seg)
    seg = _ITALIC.sub(lambda x: f"<i>{x.group(1) or x.group(2)}</i>", seg)
    parts.append(seg)
    return "".join(parts)


def format_html(text: str) -> str:
    """Convert LLM markdown response to Telegram HTML."""
    parts, last = [], 0
    for m in _FENCE.finditer(text):
        parts.append(_inline(text[last:m.start()]))
        parts.append(f"<pre><code>{_esc(m.group(1).rstrip())}</code></pre>")
        last = m.end()
    parts.append(_inline(text[last:]))
    return "".join(parts)


# ── Message processing ────────────────────────────────────────────────────

def _process(msg: dict, state, token: str, allowed: set) -> None:
    """Handle one incoming Telegram message."""
    chat_id  = msg["chat"]["id"]
    username = (msg.get("from", {}).get("username") or "").lower()
    raw      = (msg.get("text") or "").strip()

    if not raw:
        return
    if allowed and username not in allowed:
        return
    if _BOT_MSG.match(raw):  # ignore messages from other instances
        return

    # persist chat_id on first message if not already saved
    if not _load_chat_id(state):
        _save_chat_id(state, chat_id)

    sender  = msg.get("from", {})
    user_id = sender.get("id", 0)
    name    = sender.get("username") or sender.get("first_name") or str(user_id)
    _completer.erase_prompt()  # clear ❯ line before writing
    sys.stdout.write(f"{_col.input_bg} {_col.dim}✉  @{name}:\033[39m  {raw}\x1b[K\x1b[0m\r\n")
    sys.stdout.flush()

    # Resolve skill if message starts with /
    prompt = raw
    if raw.startswith("/") and raw not in ("/start",):
        resolved = _skills.load(raw, state.config.config_loader)
        if resolved is not None:
            prompt = resolved

    _save_chat_id(state, chat_id)
    history = _histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": prompt})

    with _lock:
        request    = state.request_counter.request
        model_name = state.api_client.model
        spinner    = Spinner(state.config.provider, model_name, request)
        spinner.start()
        try:
            data, elapsed = state.api_client.generate_chat(
                history,
                system_instruction=build_system_instruction(
                    state.config.system_instruction or "", state.shell_mode
                ),
            )
        except (KeyboardInterrupt, APIError):
            spinner.stop()
            history.pop()
            return
        finally:
            spinner.stop()

        token_in, token_out = state.api_client.extract_usage(data)
        if token_in:  state.total_in  += token_in
        if token_out: state.total_out += token_out
        state.total_elapsed += elapsed

        try:
            reply = state.api_client.extract_response(data)
        except ValueError:
            history.pop()
            return

        history.append({"role": "assistant", "content": reply})
        state.logger.log_user(prompt)
        state.logger.log_assistant(reply, model_name, token_in, token_out, elapsed)
        state.request_counter.request += 1

        # Skip printing initial reply when shell commands present — agentic_loop prints them
        has_cmds = state.shell_mode and bool(extract_commands(reply))
        if not has_cmds:
            highlighted = ct.highlight(reply).replace("\n", "\r\n")
            sys.stdout.write(f"\r\n {_col.marker}{sym.ai_marker}{_R} {highlighted}\r\n\r\n")
            sys.stdout.flush()
            ui.print_stats(token_in, token_out, elapsed, request)

        if state.shell_mode:
            _orig = sys.stdout
            sys.stdout = _CRLFStdout(_orig)
            try:
                state.total_in, state.total_out, state.total_elapsed, reply = agentic_loop(
                    history, reply, state.api_client, state.config, state.logger,
                    state.request_counter, state.shell_mode,
                    state.total_in, state.total_out, state.total_elapsed,
                    verbose=state.verbose,
                )
            finally:
                sys.stdout = _orig

    _completer.redraw_prompt()  # restore ❯ after all output
    _send(token, chat_id, f"@{_instance_id}: {format_html(reply)}")


# ── Notifications ─────────────────────────────────────────────────────────

def _notify(token: str, chat_id: int, key: str) -> None:
    """Send localized connect/disconnect notification with program name, version, and instance id."""
    from .version import get_project_meta, get_version
    name, _ = get_project_meta()
    ver     = get_version()
    user    = f"{name} v{ver} at {_instance_id}"
    _send(token, chat_id, t('common', key, id=user))


def _chat_id_path(state):
    """Return path to .tg_chat file stored next to ai.ini."""
    from pathlib import Path
    return Path(state.config.config_loader.config_path).parent / ".tg_chat"


def _load_chat_id(state) -> int | None:
    """Return chat_id from .tg_chat file, then ai.ini [telegram] chat_id, or None."""
    try:
        raw = _chat_id_path(state).read_text().strip()
        if raw.lstrip("-").isdigit():
            return int(raw)
    except Exception:
        pass
    # fallback: read from ai.ini
    try:
        raw = str(state.config.config_loader.get("telegram", "chat_id", default="")).strip()
        if raw.lstrip("-").isdigit():
            return int(raw)
    except Exception:
        pass
    return None


def _save_chat_id(state, chat_id: int) -> None:
    """Persist chat_id to .tg_chat file."""
    try:
        _chat_id_path(state).write_text(str(chat_id))
    except Exception:
        pass


def _bootstrap_chat_id(token: str, state) -> int | None:
    """Try to find chat_id from pending updates (timeout=0, no long-poll)."""
    try:
        r = requests.get(_BASE.format(token=token, method="getUpdates"),
                         params={"timeout": 0}, timeout=(5, 10))
        updates = r.json().get("result", []) if r.json().get("ok") else []
        for upd in reversed(updates):
            if "message" in upd:
                cid = upd["message"]["chat"]["id"]
                _save_chat_id(state, cid)
                return cid
    except requests.exceptions.ConnectionError:
        print(f" {_col.error}telegram: service unavailable{_R}", file=sys.stderr)
    except Exception:
        pass
    return None


# ── Polling loop ──────────────────────────────────────────────────────────

def _loop(state) -> None:
    """Poll Telegram for updates and dispatch messages until interrupted."""
    cfg     = state.config.config_loader
    token   = cfg.get("telegram", "token", default="").strip()
    raw_ids = cfg.get("telegram", "allowed_ids", default="")
    if not token:
        print(f" {_col.error}telegram: token not set in [telegram] ai.ini{_R}", file=sys.stderr)
        return
    allowed = {x.strip().lstrip("@").lower() for x in str(raw_ids).split(",") if x.strip().lstrip("@")}

    offset = 0
    available = True  # track connection state to print status changes once
    while True:
        try:
            updates = _get_updates(token, offset)
            if updates is None:  # ConnectionError signal from _get_updates
                if available:
                    print(f" {_col.error}telegram: service unavailable{_R}", file=sys.stderr)
                    available = False
                time.sleep(5)
                continue
            if not available:
                print(f" {_col.dim}telegram: reconnected{_R}", file=sys.stderr)
                available = True
            if not updates:
                time.sleep(1)
                continue
            for upd in updates:
                offset = upd["update_id"] + 1
                if "message" in upd:
                    _process(upd["message"], state, token, allowed)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f" {_col.error}telegram loop error: {e}{_R}", file=sys.stderr)
            time.sleep(5)


def run(state) -> None:
    """Run polling loop in main thread (--telegram mode)."""
    token   = state.config.config_loader.get("telegram", "token", default="").strip()
    print(f" {_col.dim}{t('common','tg_started')}{_R}")
    chat_id = _load_chat_id(state) or _bootstrap_chat_id(token, state)
    try:
        if token and chat_id:
            _notify(token, chat_id, 'tg_connected')
        _loop(state)
    except KeyboardInterrupt:
        if token and chat_id:
            _notify(token, chat_id, 'tg_disconnected')
        print(f"\n {_col.dim}{t('common','tg_stopped')}{_R}")


def start_thread(state) -> threading.Thread:
    """Start polling loop as a background daemon thread (/telegram command)."""
    import atexit
    token   = state.config.config_loader.get("telegram", "token", default="").strip()
    print(f" {_col.dim}{t('common','tg_started')}{_R}")
    chat_id = _load_chat_id(state) or _bootstrap_chat_id(token, state)
    if token and chat_id:
        try:
            _notify(token, chat_id, 'tg_connected')
        except (Exception, KeyboardInterrupt):
            pass
    def _on_exit():
        cid = _load_chat_id(state)
        if token and cid:
            _notify(token, cid, 'tg_disconnected')
    atexit.register(_on_exit)
    th = threading.Thread(target=_loop, args=(state,), daemon=True)
    th.start()
    return th
