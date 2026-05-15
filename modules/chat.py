"""Interactive REPL loop."""
import sys
import json
from . import text as ct
from . import colors as _col
from .state import AppState
from .spinner import Spinner
from .logo import print_logo
from .agent import agentic_loop, build_system_instruction
from .shell import extract_commands
from . import commands, ui
from . import symbols as sym
from .locale import t
from . import completer as _completer
from providers import APIError

_R = ct.resetcolor


def run(state: AppState):
    """Run interactive chat loop — handles input, slash commands, and agent dispatch."""
    cfg = state.config.config_loader

    ui.print_startup_line()

    # Show logo if enabled in config
    if cfg.get("ui", "logo", default=True):
        print_logo(
            state.config.base_dir / "logo.ascii",
            delay=cfg.get("ui", "logo_delay", default=0.02),
            logo_gradient=cfg.get("ui", "logo_gradient", default=0.25)
            )

    ui.print_banner(state.config.provider, state.api_client.model, state.shell_mode, state.verbose, state.telegram)

    history = []

    while True:
        try:
            prompt = f"{_col.input_bg} {_col.prompt}{sym.user_prompt}\033[39m  "
            raw = _completer.read_input(prompt, cfg).strip()
        except (KeyboardInterrupt, EOFError):
            ui.print_chat_totals(state.total_in, state.total_out, state.total_elapsed)
            break

        if not raw:
            continue

        # Route slash commands to handler before sending to LLM
        if raw.startswith("/"):
            result = commands.handle(raw, history, state)
            if result == "quit":
                ui.print_chat_totals(state.total_in, state.total_out, state.total_elapsed)
                break
            if result == "reset":
                history = []
                print(f" {_col.dim}{t('common','history_cleared')}{_R}")
                continue
            if result is None:
                continue
            raw = result  # skill content — fall through to LLM call

        history.append({"role": "user", "content": raw})

        # Send user message to LLM
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
        except KeyboardInterrupt:
            spinner.stop()
            history.pop()
            print(f"\n {_col.error}{t('common','interrupted')}{_R}")
            continue
        except APIError:
            spinner.stop()
            history.pop()
            continue
        finally:
            spinner.stop()

        # Accumulate session token totals
        token_in, token_out = state.api_client.extract_usage(data)
        if token_in:  state.total_in  += token_in
        if token_out: state.total_out += token_out
        state.total_elapsed += elapsed

        try:
            text = state.api_client.extract_response(data)
        except ValueError:
            print(json.dumps(data, ensure_ascii=False, indent=2), file=sys.stderr)
            history.pop()
            continue

        has_cmds = state.shell_mode and bool(extract_commands(text))
        if not has_cmds:
            print(f"\n {_col.marker}{sym.ai_marker}{_R} {ct.highlight(text)}")
            print()
            ui.print_stats(token_in, token_out, elapsed, request)

        history.append({"role": "assistant", "content": text})
        state.logger.log_user(raw)
        state.logger.log_assistant(text, model_name, token_in, token_out, elapsed)
        state.request_counter.request += 1

        # Run agent loop if shell commands were detected in the response
        if state.shell_mode:
            state.total_in, state.total_out, state.total_elapsed, _ = agentic_loop(
                history, text, state.api_client, state.config, state.logger,
                state.request_counter, state.shell_mode, state.total_in, state.total_out, state.total_elapsed,
                verbose=state.verbose,
            )
