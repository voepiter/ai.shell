"""Language detection and translated string lookup."""
import os
import locale as _locale
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

_LOCALES = Path(__file__).parent.parent / "locales"


def _detect_lang() -> str:
    for var in ("LANGUAGE", "LANG", "LC_ALL", "LC_MESSAGES"):
        val = os.environ.get(var, "")
        if val:
            code = val.split("_")[0].split(".")[0].lower()
            if code and code not in ("c", "posix"):
                return code
    try:
        loc = _locale.getdefaultlocale()[0] or ""
        if loc:
            return loc.split("_")[0].lower()
    except Exception:
        pass
    return "en"


def _load(lang: str) -> dict:
    for code in (lang, "en"):
        path = _LOCALES / f"{code}.toml"
        if path.exists():
            with open(path, "rb") as f:
                return tomllib.load(f)
    return {}


_strings = _load(_detect_lang())


def set_lang(lang: str) -> str:
    """Load strings for lang code (falls back to en); return resolved code."""
    global _strings
    for code in (lang, "en"):
        path = _LOCALES / f"{code}.toml"
        if path.exists():
            with open(path, "rb") as f:
                _strings = tomllib.load(f)
            return code
    return "en"


def t(*keys: str, **fmt) -> str:
    """Look up translated string by section + key; format with kwargs."""
    val = _strings
    for k in keys:
        if not isinstance(val, dict):
            return keys[-1]
        val = val.get(k, "")
    s = val if isinstance(val, str) else keys[-1]
    return s.format(**fmt) if fmt else s
