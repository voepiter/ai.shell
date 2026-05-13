"""Configuration — TOML file loader, typed runtime config, and config migration."""
import os
import re
from pathlib import Path
from typing import Dict, Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError("tomli is required for Python < 3.11. Install: pip install tomli")


# Default paths for user-level config and logs when installed as a package
_USER_CFG    = Path.home() / ".config" / "ai-shell" / "ai.ini"
_USER_LOG    = Path.home() / ".local" / "share" / "ai-shell" / "log"
_DEFAULT_CFG = Path(__file__).parent.parent / "ai.ini.default"


class ConfigLoader:
    """Reads ai.ini (TOML); resolves path from cwd, script dir, or ~/.config/ai-shell/."""

    # Search order: cwd → script dir → user home config
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            current_dir = Path.cwd()
            script_dir  = Path(__file__).parent.parent.absolute()
            config_path = current_dir / "ai.ini"
            if not config_path.exists():
                config_path = script_dir / "ai.ini"
            if not config_path.exists():
                config_path = _USER_CFG
        self.config_path = config_path
        self.config = self._load()

    # Return empty dict on any parse error to allow graceful fallback
    def _load(self) -> Dict:
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

    def get(self, *keys, default=None):
        """Look up a nested key path in config; return default if any key is missing."""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

    # Convenience accessors for commonly used config values
    def get_connection_timeout(self, default: int = 30) -> int:
        return int(self.get("connection", "timeout", default=default))

    def get_default_provider(self, default: str = "google") -> str:
        return str(self.get("providers", "default", default=default)).lower()

    def get_default_model(self, provider: str) -> Optional[str]:
        return self.get("models", provider.lower(), default=None)

    def get_api_key(self, env_var: str) -> Optional[str]:
        val = self.get("api_keys", env_var, default=None)
        return val if val else None

    def get_system_instruction(self) -> Optional[str]:
        return self.get("system", "instruction", default=None)


# Runtime configuration assembled from args and ai.ini
class Config:
    def __init__(
        self,
        provider:           Optional[str] = None,
        model:              Optional[str] = None,
        system_instruction: Optional[str] = None,
    ):
        self.base_dir = Path(__file__).parent.parent.absolute()
        # Use user home log dir when running from an installed package
        _installed    = "site-packages" in str(self.base_dir)
        self.log_dir  = _USER_LOG if _installed else self.base_dir / "log"
        self.config_loader = ConfigLoader()

        self.provider = (provider or self.config_loader.get_default_provider()).lower()
        self.model    = model or self.config_loader.get_default_model(self.provider)
        self.timeout  = self.config_loader.get_connection_timeout()

        self.system_instruction = system_instruction or self.config_loader.get_system_instruction() or ""


def _raw_lines(path: Path) -> Dict[str, Dict[str, str]]:
    """Parse a config file and return {section: {key: raw_line}} for migration."""
    result: Dict[str, Dict[str, str]] = {}
    section = None
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1]
            result.setdefault(section, {})
        elif section and "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=")[0].strip()
            result[section][key] = line
    return result


def _insert_into_section(content: str, section: str, lines: list) -> str:
    """Append lines at the end of a named section in config file text."""
    added = "\n".join(lines)
    m = re.search(rf"^\[{re.escape(section)}\]", content, re.M)
    if not m:
        # Section absent — append at end of file
        return content.rstrip() + f"\n\n[{section}]\n{added}\n"
    rest = content[m.end():]
    next_m = re.search(r"^\[", rest, re.M)
    if next_m:
        insert_at = m.end() + next_m.start()
        return content[:insert_at].rstrip() + f"\n{added}\n\n" + content[insert_at:]
    return content.rstrip() + f"\n{added}\n"


def migrate_config(config_loader) -> None:
    """Add keys from ai.ini.default that are missing from the user's ai.ini."""
    user_path = config_loader.config_path
    if not user_path.exists() or not _DEFAULT_CFG.exists():
        return

    with open(user_path, "rb") as f:
        user_cfg = tomllib.load(f)
    with open(_DEFAULT_CFG, "rb") as f:
        default_cfg = tomllib.load(f)

    default_raw = _raw_lines(_DEFAULT_CFG)

    # Collect raw lines for keys present in default but absent in user config
    missing: Dict[str, list] = {}
    for section, values in default_cfg.items():
        if not isinstance(values, dict):
            continue
        for key in values:
            if key not in (user_cfg.get(section) or {}):
                raw = default_raw.get(section, {}).get(key)
                if raw:
                    missing.setdefault(section, []).append(raw)

    if not missing:
        return

    content = user_path.read_text()
    for section, lines in missing.items():
        content = _insert_into_section(content, section, lines)
    user_path.write_text(content)
