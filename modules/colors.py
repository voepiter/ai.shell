# Named color palette — loaded from ai.ini [color] section
from .config import ConfigLoader

# Build ANSI 256-color foreground escape sequence
def _fg(n: int) -> str: return f"\033[38;5;{n}m"

# Build ANSI 256-color background escape sequence
def _bg(n: int) -> str: return f"\033[48;5;{n}m"

_cfg = ConfigLoader()
_c   = lambda key, default: int(_cfg.get("color", key, default=default))

# ui / cli colors
accent    = _fg(_c("accent",    99))   # purple  — borders / accents
provider  = _fg(_c("provider",  214))  # orange  — provider name
model     = _fg(_c("model",     157))  # green   — model / numbers
command   = _fg(_c("command",   75))   # cyan    — commands / prompt
dim       = _fg(_c("dim",       243))  # grey    — secondary text
marker    = _fg(_c("marker",    141))  # lavender— AI marker (✨)
error     = _fg(_c("error",     196))  # red     — errors

# highlight() colors
bold      = _fg(_c("bold",      157))  # **bold** markdown
bash      = _fg(_c("bash",      75))   # ▸ bash command lines
code_bg   = _bg(_c("code_bg",   233))  # code block background
code_lang = _fg(_c("code_lang", 243))  # code block language label
code_body = _fg(_c("code_body", 215))  # code block content
inline    = _fg(_c("inline",    222))  # `inline code`
