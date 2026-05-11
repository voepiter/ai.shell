# Chat slash-command handler (/model, /provider, /agent, /shell, /help, /quit …)
import json
import sys
from pathlib import Path
from . import colors as _col
from . import text as ct
from . import symbols as sym
from .api import APIFactory
from . import ui
from . import locale as _locale
from .locale import t

_R = ct.resetcolor


def handle(raw: str, history: list, state) -> str | None:
    # state: AppState — .config, .api_client, .shell_mode
    parts = raw.split(maxsplit=1)
    cmd   = parts[0].lower()
    arg   = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit", "/q"):
        return "quit"

    if cmd in ("/help", "/?"):
        ui.print_chat_help()
        return None

    if cmd in ("/list-providers", "/lp"):
        ui.print_providers(state.config.config_loader)
        return None

    if cmd in ("/list-models", "/lm"):
        ui.print_models(state.config.provider, state.api_client, state.config.config_loader)
        return None

    if cmd == "/model":
        if not arg:
            print(f" {_col.error}{t('commands','usage_model')}{_R}", file=sys.stderr)
            return None
        try:
            state.config.model = arg
            state.api_client   = APIFactory.create_client(
                provider=state.config.provider,
                model=arg,
                timeout=state.config.timeout,
            )
            ui.print_current_status(state.config.provider, state.api_client.model)
        except ValueError as e:
            print(f" {_col.error}{e}{_R}", file=sys.stderr)
        return None

    if cmd == "/provider":
        if not arg:
            print(f" {_col.error}{t('commands','usage_provider')}{_R}", file=sys.stderr)
            return None
        try:
            state.config.provider = arg.lower()
            state.config.model    = state.config.config_loader.get_default_model(state.config.provider)
            state.api_client = APIFactory.create_client(
                provider=state.config.provider,
                model=state.config.model,
                timeout=state.config.timeout,
            )
            ui.print_current_status(state.config.provider, state.api_client.model)
            return "reset"
        except ValueError as e:
            print(f" {_col.error}{e}{_R}", file=sys.stderr)
        return None

    if cmd == "/shell":
        state.shell_mode = not state.shell_mode
        status = f"{_col.model}on{_R}" if state.shell_mode else f"{_col.dim}off{_R}"
        print(f" {_col.dim}{t('commands','shell_agent')} {sym.arrow}{_R} {status}")
        return None

    if cmd == "/language":
        if not arg:
            print(f" {_col.error}{t('commands','usage_language')}{_R}", file=sys.stderr)
            return None
        resolved = _locale.set_lang(arg)
        print(f" {_col.dim}{t('commands','language_set',lang=resolved)}{_R}")
        return None

    if cmd in ("/usage", "/u"):
        ui.print_usage(state.total_in, state.total_out, state.total_elapsed)
        return None

    if cmd in ("/clear", "/cls"):
        return "reset"

    if cmd == "/verbose":
        state.verbose = (arg == "true") if arg in ("true", "false") else not state.verbose
        status = f"{_col.model}on{_R}" if state.verbose else f"{_col.dim}off{_R}"
        print(f" {_col.dim}verbose {sym.arrow}{_R} {status}")
        return None

    if cmd == "/sessions":
        _cmd_sessions(state.config.log_dir)
        return None

    if cmd == "/resume":
        if not arg:
            print(f" {_col.error}usage: /resume <session_id>{_R}", file=sys.stderr)
            return None
        _cmd_resume(arg, history, state.config.log_dir)
        return None

    print(f" {_col.error}{t('commands','unknown_cmd',cmd=cmd)}{_R}", file=sys.stderr)
    return None


def _cmd_sessions(log_dir: Path) -> None:
    files = sorted(log_dir.glob("*.jsonl"), reverse=True)[:10]
    if not files:
        print(f" {_col.dim}no sessions found{_R}")
        return
    print(f"\n {_col.dim}{'ID':<20} {'Model':<22} Last prompt{_R}")
    print(f" {_col.dim}{'-'*20} {'-'*22} {'-'*40}{_R}")
    for f in files:
        session_id = f.stem
        last_user  = ""
        model      = ""
        try:
            with f.open(encoding="utf-8") as fh:
                for raw in fh:
                    rec = json.loads(raw)
                    if rec.get("role") == "user" and not rec.get("tool"):
                        last_user = rec.get("content", "")
                    elif rec.get("role") == "assistant" and not model:
                        model = rec.get("model", "")
        except Exception:
            continue
        short = (last_user[:50] + "…") if len(last_user) > 51 else last_user
        short = short.replace("\n", " ")
        print(f" {_col.model}{session_id:<20}{_R} {_col.dim}{model:<22}{_R} {short}")
    print()


def _cmd_resume(session_id: str, history: list, log_dir: Path) -> None:
    logfile = log_dir / f"{session_id}.jsonl"
    if not logfile.exists():
        print(f" {_col.error}session not found: {session_id}{_R}", file=sys.stderr)
        return
    records = []
    try:
        with logfile.open(encoding="utf-8") as f:
            for raw in f:
                records.append(json.loads(raw.strip()))
    except Exception as e:
        print(f" {_col.error}failed to read session: {e}{_R}", file=sys.stderr)
        return

    # Filter to conversation messages only (skip agent tool_msg noise)
    conv = [r for r in records if r.get("role") in ("user", "assistant")]
    if not conv:
        print(f" {_col.dim}session is empty{_R}")
        return

    print(f"\n {_col.dim}── resumed session {session_id} ({len(conv)} messages) ──{_R}\n")
    for rec in conv:
        role    = rec["role"]
        content = rec.get("content", "")
        ts      = rec.get("ts", "")
        if role == "user":
            print(f" {_col.dim}{ts}  {sym.user_prompt}{_R}  {content}")
        else:
            print(f" {_col.dim}{ts}  {sym.ai_marker}{_R}  {ct.highlight(content)}")
        print()

    history.clear()
    history.extend({"role": r["role"], "content": r["content"]} for r in conv)
    print(f" {_col.dim}history loaded — continuing conversation{_R}\n")
