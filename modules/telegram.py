"""Telegram bot integration — polling loop and LLM dispatch."""
import re
import sys
import threading
import time
import requests
from . import colors as _col
from . import text as ct
from .agent import agentic_loop, build_system_instruction
from .spinner import Spinner
from . import skills as _skills
from providers import APIError

_R    = ct.resetcolor
_BASE = "https://api.telegram.org/bot{token}/{method}"
_lock = threading.Lock()  # serialise LLM calls

_histories: dict[int, list] = {}  # per chat_id conversation history


# ── Telegram API helpers ──────────────────────────────────────────────────

def _api_post(token: str, method: str, **kwargs) -> dict | None:
    """POST to Telegram Bot API; return JSON or None on error."""
    url = _BASE.format(token=token, method=method)
    try:
        r = requests.post(url, json=kwargs, timeout=35)
        return r.json()
    except Exception as e:
        print(f" {_col.error}tg: {e}{_R}", file=sys.stderr)
        return None


def _send(token: str, chat_id: int, text: str) -> None:
    """Send HTML message; fall back to plain text on parse error."""
    res = _api_post(token, "sendMessage", chat_id=chat_id,
                    text=text, parse_mode="HTML")
    if res and not res.get("ok"):
        _api_post(token, "sendMessage", chat_id=chat_id, text=text)


def _get_updates(token: str, offset: int) -> list:
    """Long-poll getUpdates; return list of updates or [] on error."""
    url = _BASE.format(token=token, method="getUpdates")
    try:
        r = requests.get(url, params={"offset": offset, "timeout": 30},
                         timeout=35)
        d = r.json()
        return d.get("result", []) if d.get("ok") else []
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
    chat_id = msg["chat"]["id"]
    user_id = msg.get("from", {}).get("id", 0)
    raw     = (msg.get("text") or "").strip()

    if not raw:
        return
    if allowed and user_id not in allowed:
        return

    print(f" {_col.dim}tg [{user_id}]: {raw[:70]}{_R}")

    # Resolve skill if message starts with /
    prompt = raw
    if raw.startswith("/") and raw not in ("/start",):
        resolved = _skills.load(raw, state.config.config_loader)
        if resolved is not None:
            prompt = resolved

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

        if state.shell_mode:
            state.total_in, state.total_out, state.total_elapsed, reply = agentic_loop(
                history, reply, state.api_client, state.config, state.logger,
                state.request_counter, state.shell_mode,
                state.total_in, state.total_out, state.total_elapsed,
                verbose=state.verbose,
            )

    _send(token, chat_id, format_html(reply))


# ── Polling loop ──────────────────────────────────────────────────────────

def _loop(state) -> None:
    """Poll Telegram for updates and dispatch messages until interrupted."""
    cfg     = state.config.config_loader
    token   = cfg.get("telegram", "token", default="").strip()
    raw_ids = cfg.get("telegram", "allowed_ids", default="")
    if not token:
        print(f" {_col.error}telegram: token not set in [telegram] ai.ini{_R}", file=sys.stderr)
        return
    allowed = {int(x.strip()) for x in str(raw_ids).split(",") if x.strip().lstrip("-").isdigit()}

    print(f" {_col.dim}telegram bot started (ctrl+c to stop){_R}")
    offset = 0
    while True:
        updates = _get_updates(token, offset)
        if not updates:
            time.sleep(1)  # back-off on network errors
            continue
        for upd in updates:
            offset = upd["update_id"] + 1
            if "message" in upd:
                _process(upd["message"], state, token, allowed)


def run(state) -> None:
    """Run polling loop in main thread (--telegram mode)."""
    try:
        _loop(state)
    except KeyboardInterrupt:
        print(f"\n {_col.dim}telegram bot stopped{_R}")


def start_thread(state) -> threading.Thread:
    """Start polling loop as a background daemon thread (/telegram command)."""
    t = threading.Thread(target=_loop, args=(state,), daemon=True)
    t.start()
    return t
