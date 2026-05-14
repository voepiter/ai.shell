"""Slash-command dispatcher for interactive chat (/help, /model, /provider, /shell, /verbose, /sessions, /resume …)."""
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
from . import skills as _skills

_R = ct.resetcolor


def handle(raw: str, history: list, state) -> str | None:
    """Route slash command to handler; return 'quit', 'reset', or None."""
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
            # Switch provider and reset to its default model
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
        # Accept explicit true/false or toggle if no arg given
        state.verbose = (arg == "true") if arg in ("true", "false") else not state.verbose
        status = f"{_col.model}on{_R}" if state.verbose else f"{_col.dim}off{_R}"
        print(f" {_col.dim}verbose {sym.arrow}{_R} {status}")
        return None

    if cmd == "/skill" and not arg:
        _cmd_skills(state.config.config_loader)
        return None

    if cmd == "/sessions":
        _cmd_sessions(state.config.log_dir)
        return None

    if cmd == "/resume":
        if not arg:
            print(f" {_col.error}{t('commands','usage_resume')}{_R}", file=sys.stderr)
            return None
        _cmd_resume(arg, history, state.config.log_dir)
        return None

    # Try to resolve as a skill before reporting unknown command
    content = _skills.load(raw, state.config.config_loader)
    if content is not None:
        return content
    print(f" {_col.error}{t('commands','unknown_cmd',cmd=cmd)}{_R}", file=sys.stderr)
    return None


def _cmd_skills(config_loader) -> None:
    """Print table of available skills with descriptions."""
    items = _skills.list_skills(config_loader)
    if not items:
        print(f" {_col.dim}{t('skills','no_skills')}{_R}")
        return
    print(f"\n {_col.dim}{t('skills','header')}{_R}")
    for name, desc in items:
        print(f"  {_col.command}/{name:<18}{_R} {_col.dim}{desc}{_R}")
    print()


def _cmd_sessions(log_dir: Path) -> None:
    """Print table of 10 most recent sessions from JSONL logs."""
    files = sorted(log_dir.glob("*.jsonl"), reverse=True)[:10]
    if not files:
        print(f" {_col.dim}{t('commands','no_sessions')}{_R}")
        return

    col_id     = t('commands', 'sessions_col_id')
    col_model  = t('commands', 'sessions_col_model')
    col_prompt = t('commands', 'sessions_col_prompt')
    print(f"\n {_col.dim}{col_id:<20} {col_model:<22} {col_prompt}{_R}")
    print(f" {_col.dim}{'-'*20} {'-'*22} {'-'*50}{_R}")

    # Tool messages start with these prefixes — skip them when finding last user prompt
    _TOOL_PREFIXES = ("Command output:", "Вывод команды:")
    for f in files:
        session_id = f.stem
        last_user  = ""
        model      = ""
        try:
            with f.open(encoding="utf-8") as fh:
                for raw in fh:
                    rec = json.loads(raw)
                    if rec.get("role") == "user":
                        content = rec.get("content", "")
                        is_tool = rec.get("tool") or content.startswith(_TOOL_PREFIXES)
                        if not is_tool:
                            last_user = content
                    elif rec.get("role") == "assistant" and not model:
                        model = rec.get("model", "")
        except Exception:
            continue
        short = (last_user[:70] + "…") if len(last_user) > 71 else last_user
        short = short.replace("\n", " ")
        print(f" {_col.model}{session_id:<20}{_R} {_col.dim}{model:<22}{_R} {short}")
    print()


def _cmd_resume(session_id: str, history: list, log_dir: Path) -> None:
    """Load session history into active conversation and display transcript."""
    logfile = log_dir / f"{session_id}.jsonl"
    if not logfile.exists():
        print(f" {_col.error}{t('commands','session_not_found',id=session_id)}{_R}", file=sys.stderr)
        return

    # Parse all JSONL records from the session file
    records = []
    try:
        with logfile.open(encoding="utf-8") as f:
            for raw in f:
                records.append(json.loads(raw.strip()))
    except Exception as e:
        print(f" {_col.error}{t('commands','session_read_error',e=e)}{_R}", file=sys.stderr)
        return

    # Filter to conversation messages only (skip agent tool_msg noise)
    conv = [r for r in records if r.get("role") in ("user", "assistant")]
    if not conv:
        print(f" {_col.dim}{t('commands','session_empty')}{_R}")
        return

    # Display transcript
    print(f"\n {_col.dim}{t('commands','resumed_session',id=session_id,n=len(conv))}{_R}\n")
    for rec in conv:
        role    = rec["role"]
        content = rec.get("content", "")
        ts      = rec.get("ts", "")
        if role == "user":
            print(f" {_col.dim}{ts}  {sym.user_prompt}{_R}  {content}")
        else:
            print(f" {_col.dim}{ts}  {sym.ai_marker}{_R}  {ct.highlight(content)}")
        print()

    # Replace active history with loaded session
    history.clear()
    history.extend({"role": r["role"], "content": r["content"]} for r in conv)
    print(f" {_col.dim}{t('commands','history_loaded')}{_R}\n")
