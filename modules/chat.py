# Interactive chat loop
import sys
import json
from . import text as ct
from . import colors as _col
from .state import AppState
from .spinner import Spinner
from .logo import print_logo
from .agent import agentic_loop, build_system_instruction
from . import commands, ui
from . import symbols as sym
from .locale import t
from providers import APIError

_R = ct.resetcolor


def run(state: AppState):
    cfg = state.config.config_loader
    if cfg.get("ui", "logo", default=True):
        print_logo(
            state.config.base_dir / "logo.ascii",
            delay=cfg.get("ui", "logo_delay", default=0.02),
            logo_gradient=cfg.get("ui", "logo_gradient", default=0.25)
            )

    ui.print_banner(state.config.provider, state.api_client.model, state.shell_mode)

    history       = []
    total_in      = 0
    total_out     = 0
    total_elapsed = 0.0

    while True:
        try:
            # \001/\002 tell readline the true visible width of the escape codes
            prompt = f"\n \001{_col.command}\002{sym.user_prompt}\001{_R}\002  "
            raw = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            ui.print_chat_totals(total_in, total_out, total_elapsed)
            break

        if not raw:
            continue

        if raw.startswith("/"):
            result = commands.handle(raw, history, state)
            if result == "quit":
                ui.print_chat_totals(total_in, total_out, total_elapsed)
                break
            if result == "reset":
                history, total_in, total_out, total_elapsed = [], 0, 0, 0.0
                print(f" {_col.dim}{t('common','history_cleared')}{_R}")
            continue

        history.append({"role": "user", "content": raw})

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

        token_in, token_out = state.api_client.extract_usage(data)
        if token_in:  total_in  += token_in
        if token_out: total_out += token_out
        total_elapsed += elapsed

        try:
            text = state.api_client.extract_response(data)
        except ValueError:
            print(json.dumps(data, ensure_ascii=False, indent=2), file=sys.stderr)
            history.pop()
            continue

        print(f"\n {_col.marker}{sym.ai_marker}{_R}  {ct.highlight(text)}")
        print()
        ui.print_stats(token_in, token_out, elapsed, total_in, total_out, total_elapsed)

        history.append({"role": "assistant", "content": text})
        state.logger.log_request(
            model=model_name, request=request, elapsed=elapsed,
            token_in=token_in, token_out=token_out, prompt=raw, answer=text,
        )
        state.request_counter.request += 1

        if state.shell_mode:
            total_in, total_out, total_elapsed = agentic_loop(
                history, text, state.api_client, state.config, state.logger,
                state.request_counter, state.shell_mode, total_in, total_out, total_elapsed,
            )
