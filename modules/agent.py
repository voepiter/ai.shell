# Shell agent loop — command execution and multi-step LLM iteration
from . import text as ct
from . import colors as _col
from .shell import extract_commands, is_dangerous, run_command
from .spinner import Spinner
from .ui import print_stats
from . import symbols as sym

_R = ct.resetcolor

_SHELL_HINT = (
    "You have shell access on this machine. "
    "When you need to run a command, wrap it in <bash>command</bash> tags "
    "(one command per response). You will receive the output and can continue. "
    "When done, give a final answer with no <bash> tags."
)


def build_system_instruction(base: str, shell_mode: bool) -> str:
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
) -> tuple[int, int, float]:
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
            if is_dangerous(cmd, danger_pat):
                print(f"\n {_col.error}dangerous:{_R} {cmd}")
                print(f" {_col.dim}execute? [y/N]{_R} ", end="", flush=True)
                try:
                    answer = input().strip().lower()
                except (KeyboardInterrupt, EOFError):
                    answer = "n"
                if answer != "y":
                    results.append(f"$ {cmd}\n[skipped by user]")
                    continue

            print(f" {_col.dim}{sym.computer} {cmd}{_R}")
            result = run_command(cmd, timeout=cmd_timeout)
            output = result.to_context()
            for line in output.split("\n")[1:]:
                print(f"   {line}")
            results.append(output)

        if not results:
            break

        tool_msg = "Command output:\n" + "\n\n".join(results)
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
            print(f"\n {_col.error}interrupted{_R}")
            break
        finally:
            spinner.stop()

        token_in, token_out = api_client.extract_usage(data)
        if token_in:  total_in  += token_in
        if token_out: total_out += token_out
        total_elapsed += elapsed

        try:
            text = api_client.extract_response(data)
        except ValueError:
            break

        print(f"\n {_col.marker}{sym.ai_marker}{_R}  {ct.highlight(text)}")
        print()
        print_stats(token_in, token_out, elapsed, total_in, total_out, total_elapsed)

        history.append({"role": "assistant", "content": text})
        logger.log_request(
            model=model_name, request=request, elapsed=elapsed,
            token_in=token_in, token_out=token_out,
            prompt=tool_msg, answer=text,
        )
        request_counter.request += 1

    return total_in, total_out, total_elapsed
