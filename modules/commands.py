# Chat slash-command handler (/model, /provider, /agent, /shell, /help, /quit …)
import sys
from . import colors as _col
from . import text as ct
from . import symbols as sym
from .api import APIFactory
from . import ui

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
            print(f" {_col.error}usage: /model <name>{_R}", file=sys.stderr)
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
            print(f" {_col.error}usage: /provider <name>{_R}", file=sys.stderr)
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
        state.shell_mode = (arg == "on") if arg in ("on", "off") else not state.shell_mode
        status = f"{_col.model}on{_R}" if state.shell_mode else f"{_col.dim}off{_R}"
        print(f" {_col.dim}shell agent {sym.arrow}{_R} {status}")
        return None

    print(f" {_col.error}unknown command: {cmd}  (type /help){_R}", file=sys.stderr)
    return None
