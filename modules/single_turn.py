"""Single-turn (non-interactive) request handler."""
import sys
import json
from . import text as ct
from . import colors as _col
from .state import AppState
from .spinner import Spinner
from .shell import extract_commands
from .agent import agentic_loop, build_system_instruction
from . import ui
from . import symbols as sym
from .locale import t
from providers import APIError

_R = ct.resetcolor


def run(state: AppState, prompt: str):
    """Send one prompt, print response; runs agent loop if shell commands are detected."""
    ui.print_startup_line()
    request    = state.request_counter.request
    model_name = state.api_client.model
    spinner    = Spinner(state.config.provider, model_name, request)
    spinner.start()
    try:
        data, elapsed = state.api_client.generate_content(
            prompt,
            system_instruction=build_system_instruction(
                state.config.system_instruction or "", state.shell_mode
            ),
        )
    except KeyboardInterrupt:
        print(f"\n{_col.error}{t('common','interrupted')}{_R}")
        sys.exit(130)
    except APIError:
        sys.exit(1)
    finally:
        spinner.stop()

    token_in, token_out = state.api_client.extract_usage(data)

    try:
        text = state.api_client.extract_response(data)

        # Suppress output if the agent loop will print its own response
        agent_will_run = state.shell_mode and extract_commands(text)
        if not agent_will_run:
            print(ct.highlight(text))
            ui.print_stats(token_in, token_out, elapsed)

        state.logger.log_user(prompt)
        state.logger.log_assistant(text, model_name, token_in, token_out, elapsed)
        state.request_counter.request += 1

        if agent_will_run:
            # Build minimal history so the agent loop has conversation context
            history = [
                {"role": "user",      "content": prompt},
                {"role": "assistant", "content": text},
            ]
            agentic_loop(
                history, text, state.api_client, state.config, state.logger,
                state.request_counter, state.shell_mode,
                token_in or 0, token_out or 0, elapsed,
                verbose=state.verbose,
            )
    except ValueError:
        print(json.dumps(data, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(2)
