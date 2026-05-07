# Shell command executor for agent mode
import re
import subprocess
from dataclasses import dataclass
from typing import List

BASH_RE     = re.compile(r"<bash>(.*?)</bash>", re.DOTALL | re.IGNORECASE)
MARKDOWN_RE = re.compile(r"```(?:bash|sh)\s*\n?(.*?)```", re.DOTALL)


@dataclass
class CommandResult:
    command:   str
    stdout:    str
    stderr:    str
    exit_code: int
    timed_out: bool = False

    def to_context(self) -> str:
        parts = [f"$ {self.command}"]
        if self.timed_out:
            parts.append("[timed out]")
        else:
            if self.stdout:
                parts.append(self.stdout.rstrip())
            if self.stderr:
                parts.append(f"[stderr]\n{self.stderr.rstrip()}")
            if self.exit_code != 0:
                parts.append(f"[exit {self.exit_code}]")
        return "\n".join(parts)


def extract_commands(text: str) -> List[str]:
    cmds = [m.strip() for m in BASH_RE.findall(text) if m.strip()]
    if not cmds:
        cmds = [m.strip() for m in MARKDOWN_RE.findall(text) if m.strip()]
    return cmds


def is_dangerous(command: str, patterns: List[str]) -> bool:
    lower = command.lower()
    return any(p.lower() in lower for p in patterns)


def run_command(command: str, timeout: int = 30) -> CommandResult:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return CommandResult(
            command=command,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return CommandResult(command=command, stdout="", stderr="", exit_code=-1, timed_out=True)
