"""Terminal symbols — unicode or ASCII depending on ai.ini [ui] unicode setting."""
from .config import ConfigLoader

_cfg = ConfigLoader()
_unicode = bool(_cfg.get("ui", "unicode", default=True))

def _u(uni: str, asc: str) -> str:
    return uni if _unicode else asc

ai_marker      = _u("✨",  "*")
user_prompt    = _u("🗨️", ">")
bash_prefix    = _u("▸",  ">")
computer       = _u("🖥️", "$")
arrow          = _u("→",  "->")
em_dash        = _u("—",  "-")
middle_dot     = _u("·",  ".")
bullet         = _u("•",  "*")
spinner_frames = _u("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏", "-\\|/")
