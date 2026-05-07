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


class ConfigLoader:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            current_dir = Path.cwd()
            script_dir  = Path(__file__).parent.parent.absolute()
            config_path = current_dir / "ai.ini"
            if not config_path.exists():
                config_path = script_dir / "ai.ini"
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

    def get_default_assistant(self, default: Optional[str] = None) -> Optional[str]:
        return self.get("assistant", "default", default=default)

    def get_default_model(self, provider: str) -> Optional[str]:
        return self.get("models", provider.lower(), default=None)

    def get_api_key(self, env_var: str) -> Optional[str]:
        val = self.get("api_keys", env_var, default=None)
        return val if val else None

    def get_assistant_instruction(self, assistant_name: str) -> Optional[str]:
        return self.get("assistant", assistant_name, default=None)


class Config:
    def __init__(
        self,
        provider:           Optional[str] = None,
        model:              Optional[str] = None,
        system_instruction: Optional[str] = None,
        agent_name:         Optional[str] = None,
    ):
        self.base_dir      = Path(__file__).parent.parent.absolute()
        self.logfile       = self.base_dir / "ai.log"
        self.config_loader = ConfigLoader()

        self.provider = (provider or self.config_loader.get_default_provider()).lower()
        self.model    = model or self.config_loader.get_default_model(self.provider)
        self.timeout  = self.config_loader.get_connection_timeout()

        if system_instruction:
            self.system_instruction = system_instruction
        elif agent_name:
            instr = self.config_loader.get_assistant_instruction(agent_name)
            self.system_instruction = instr or self._default_instruction()
        else:
            default_agent = self.config_loader.get_default_assistant()
            if default_agent:
                instr = self.config_loader.get_assistant_instruction(default_agent)
                self.system_instruction = instr or self._default_instruction()
            else:
                self.system_instruction = self._default_instruction()

        self.agent_name = agent_name

    def _default_instruction(self) -> str:
        return "IT expert: Linux,DevOps,Coder.short answer"
