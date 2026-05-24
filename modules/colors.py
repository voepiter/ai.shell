# Named color palette — loaded from ai.ini [color] section
from .config import ConfigLoader

# Build ANSI 256-color foreground escape sequence
def forecolor(n: int) -> str: return f"\033[38;5;{n}m"

# Build ANSI 256-color background escape sequence
def backcolor(n: int) -> str: return f"\033[48;5;{n}m"

# Reset to default terminal color
reset = "\033[0m"

_cfg = ConfigLoader()
_c   = lambda key, default: int(_cfg.get("color", key, default=default))

# ui / cli colors
accent    = forecolor(_c("accent",    99))   # purple  — borders / accents
provider  = forecolor(_c("provider",  214))  # orange  — provider name
model     = forecolor(_c("model",     157))  # green   — model / numbers
command   = forecolor(_c("command",   75))   # cyan    — commands / prompt
prompt    = forecolor(_c("prompt",   119))   # green   — chat input symbol ❯
dim       = forecolor(_c("dim",       243))  # grey    — secondary text
marker    = forecolor(_c("marker",    141))  # lavender— AI marker (✨)
error     = forecolor(_c("error",     196))  # red     — errors

# highlight() colors
bold      = forecolor(_c("bold",      157))  # **bold** markdown
bash      = forecolor(_c("bash",      75))   # ▸ bash command lines
code_bg   = backcolor(_c("code_bg",   233))  # code block background
code_lang = forecolor(_c("code_lang", 243))  # code block language label
code_body = forecolor(_c("code_body", 215))  # code block content
inline    = forecolor(_c("inline",    222))  # `inline code`
input_bg  = backcolor(_c("input_bg",  235))  # user input / telegram message line background
