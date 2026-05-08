# AppState — shared runtime state passed across all modules
from dataclasses import dataclass
from .config import Config
from .api import APIFactory
from .logger import Logger
from .counter import RequestCounter


@dataclass
class AppState:
    config:          Config
    api_client:      object   # BaseAPIClient
    logger:          Logger
    request_counter: RequestCounter
    shell_mode:      bool

    @classmethod
    def from_args(cls, args) -> "AppState":
        config = Config(
            provider=args.provider,
            model=args.model,
            system_instruction=args.instruction,
        )
        return cls(
            config          = config,
            api_client      = APIFactory.create_client(
                provider=config.provider,
                model=config.model,
                timeout=config.timeout,
                config_loader=config.config_loader,
            ),
            logger          = Logger(config.log_dir),
            request_counter = RequestCounter(config.log_dir),
            shell_mode      = bool(
                config.config_loader.get("shell", "shell_mode", default=False)
            ),
        )
