"""Shell agent loop — iterative bash command execution and LLM interaction."""
from . import text as ct
from . import colors as _col
from .shell import extract_commands, is_dangerous, run_command
from .spinner import Spinner
from .ui import print_stats
from . import symbols as sym
from .locale import t
from providers import APIError

_R = ct.resetcolor

# System prompt appended when shell mode is active
_SHELL_HINT = (
    "You have shell access on this machine. "
    "To answer questions that require running commands, execute them — do not just suggest. "
    "Wrap each command in <bash>command</bash> tags (one per response). "
    "You will receive the output and can continue reasoning. "
    "Give a final answer only after all needed commands have run."
)


def build_system_instruction(base: str, shell_mode: bool) -> str:
    """Append shell hint to system instruction when shell mode is active."""
    if not shell_mode:
        return base
    return f"{base}\n\n{_SHELL_HINT}" if base else _SHELL_HINT


def agentic_loop(
    history:       list,
    text:          str,
    api_client,
    config,
    logger,
    request_counter,
    shell_mode:    bool,
    total_in:      int,
    total_out:     int,
    total_elapsed: float = 0.0,
    verbose:       bool  = True,
) -> tuple[int, int, float, str]:
    """Run bash commands from LLM response, feed output back, repeat until no commands remain."""
    # Read shell execution limits from config
    cfg         = config.config_loader
    max_iter    = cfg.get("shell", "max_iterations",    default=5)
    cmd_timeout = cfg.get("shell", "command_timeout",   default=30)
    danger_pat  = cfg.get("shell", "dangerous_patterns", default=[])

    for _ in range(max_iter):
        commands = extract_commands(text)
        if not commands:
            break

        results = []
        for cmd in commands:
            # Prompt user before running anything matching dangerous patterns
            if is_dangerous(cmd, danger_pat):
                print(f"\n {_col.error}{t('agent','dangerous')}{_R} {cmd}")
                print(f" {_col.dim}{t('agent','execute_prompt')}{_R} ", end="", flush=True)
                try:
                    answer = input().strip().lower()
                except (KeyboardInterrupt, EOFError):
                    answer = "n"
                if answer != "y":
                    results.append(f"$ {cmd}\n{t('agent','skipped')}")
                    continue

            print(f" {_col.command}{sym.computer} {cmd}{_R}")
            result = run_command(cmd, timeout=cmd_timeout)
            output = result.to_context()
            if verbose:
                for line in output.split("\n")[1:]:
                    print(f"   {line}")
            results.append(output)

        if not results:
            break

        # Feed all command output back to the LLM as a user message
        tool_msg = f"{t('agent','cmd_output')}\n" + "\n\n".join(results)
        history.append({"role": "user", "content": tool_msg})

        model_name = api_client.model
        request    = request_counter.request
        spinner    = Spinner(config.provider, model_name, request)
        spinner.start()
        try:
            data, elapsed = api_client.generate_chat(
                history,
                system_instruction=build_system_instruction(
                    config.system_instruction or "", shell_mode
                ),
            )
        except KeyboardInterrupt:
            spinner.stop()
            history.pop()
            print(f"\n {_col.error}{t('common','interrupted')}{_R}")
            break
        except APIError:
            spinner.stop()
            history.pop()
            break
        finally:
            spinner.stop()

        # Accumulate token usage across iterations
        token_in, token_out = api_client.extract_usage(data)
        if token_in:  total_in  += token_in
        if token_out: total_out += token_out
        total_elapsed += elapsed

        try:
            text = api_client.extract_response(data)
        except ValueError:
            break

        print(f" {_col.marker}{sym.ai_marker}{_R} {ct.highlight(text)}")
        print_stats(token_in, token_out, elapsed, request)

        history.append({"role": "assistant", "content": text})
        logger.log_tool(tool_msg)
        logger.log_assistant(text, model_name, token_in, token_out, elapsed)
        request_counter.request += 1

    return total_in, total_out, total_elapsed, text
