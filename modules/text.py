"""Terminal text rendering — ANSI colors and markdown highlighting."""
import re
from . import colors as _col
from . import symbols as sym

resetcolor = "\033[0m"


def forecolor(color: int) -> str:
    return f"\033[38;5;{color}m"


def backcolor(color: int) -> str:
    return f"\033[48;5;{color}m"


def highlight(text: str) -> str:
    # **bold**
    text = re.sub(
        r"\*\*([^*]+)\*\*",
        lambda m: f"{_col.bold}{m.group(1)}{resetcolor}",
        text,
    )

    def _fmt_bash(code: str) -> str:
        lines = [l for l in code.strip().splitlines() if l.strip()]
        return "\n".join(f"{_col.bash}{sym.bash_prefix} {l}{resetcolor}" for l in lines) if lines else ""

    # <bash> execution tags
    text = re.sub(
        r"<bash>(.*?)</bash>",
        lambda m: _fmt_bash(m.group(1)),
        text,
        flags=re.S | re.IGNORECASE,
    )

    # ```bash blocks (display only)
    text = re.sub(
        r"```bash\s*\n?(.*?)```",
        lambda m: _fmt_bash(m.group(1)),
        text,
        flags=re.S,
    )

    # other code blocks
    text = re.sub(
        r"```([a-zA-Z0-9_-]+)\s*\n?(.*?)```",
        lambda m: (
            f"{_col.code_bg}{_col.code_lang}{m.group(1)}{resetcolor}\n"
            f"{_col.code_bg}{_col.code_body}{m.group(2)}{resetcolor}"
        ),
        text,
        flags=re.S,
    )

    # `inline code`
    text = re.sub(
        r"`([^`]+)`",
        lambda m: f"{_col.inline}{m.group(1)}{resetcolor}",
        text,
    )

    # убираем * в начале строки
    text = re.sub(r"^\*+", "", text, flags=re.M)

    return text
