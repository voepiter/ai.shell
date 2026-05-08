# Configuration — file loader (ConfigLoader) and app config (Config)
import os
from pathlib import Path
from typing import Dict, Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError("tomli is required for Python < 3.11. Install: pip install tomli")


_USER_CFG = Path.home() / ".config" / "ai-shell" / "ai.ini"
_USER_LOG = Path.home() / ".local" / "share" / "ai-shell" / "log"


class ConfigLoader:
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

    def _load(self) -> Dict:
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

    def get(self, *keys, default=None):
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

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


class Config:
    def __init__(
        self,
        provider:           Optional[str] = None,
        model:              Optional[str] = None,
        system_instruction: Optional[str] = None,
    ):
        self.base_dir = Path(__file__).parent.parent.absolute()
        _installed    = "site-packages" in str(self.base_dir)
        self.log_dir  = _USER_LOG if _installed else self.base_dir / "log"
        self.config_loader = ConfigLoader()

        self.provider = (provider or self.config_loader.get_default_provider()).lower()
        self.model    = model or self.config_loader.get_default_model(self.provider)
        self.timeout  = self.config_loader.get_connection_timeout()

        self.system_instruction = system_instruction or self.config_loader.get_system_instruction() or ""
