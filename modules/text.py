"""Terminal text rendering — ANSI colors and markdown highlighting."""
import re
from . import colors as _col
from . import symbols as sym


# Format bash code block as colored prefixed command lines
def _fmt_bash(code: str) -> str:
    lines = [line for line in code.strip().splitlines() if line.strip()]
    return "\n".join(f"{_col.bash}{sym.bash_prefix} {line}{_col.reset}" for line in lines) if lines else ""


# Apply ANSI color formatting to markdown-style syntax in LLM output
def highlight(text: str) -> str:
    # **bold**
    text = re.sub(
        r"\*\*([^*]+)\*\*",
        lambda m: f"{_col.bold}{m.group(1)}{_col.reset}",
        text,
    )

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

    # Other fenced code blocks with language label
    text = re.sub(
        r"```([a-zA-Z0-9_-]+)\s*\n?(.*?)```",
        lambda m: (
            f"{_col.code_bg}{_col.code_lang}{m.group(1)}{_col.reset}\n"
            f"{_col.code_bg}{_col.code_body}{m.group(2)}{_col.reset}"
        ),
        text,
        flags=re.S,
    )

    # `inline code`
    text = re.sub(
        r"`([^`]+)`",
        lambda m: f"{_col.inline}{m.group(1)}{_col.reset}",
        text,
    )

    # Strip leading asterisks used as markdown list bullets
    text = re.sub(r"^\*+", "", text, flags=re.M)

    return text
