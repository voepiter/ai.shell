"""Shared runtime state passed across all modules."""
from dataclasses import dataclass
from .config import Config
from .api import APIFactory
from .logger import Logger
from .counter import RequestCounter


# Central state object passed to chat, single_turn, and agent modules
@dataclass
class AppState:
    config:          Config
    api_client:      object   # BaseAPIClient
    logger:          Logger
    request_counter: RequestCounter
    shell_mode:      bool
    verbose:         bool  = True
    telegram:        bool  = False
    total_in:        int   = 0
    total_out:       int   = 0
    total_elapsed:   float = 0.0

    @classmethod
    def from_args(cls, args) -> "AppState":
        """Build AppState from parsed CLI args and ai.ini config."""
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
            request_counter = RequestCounter(),
            shell_mode      = bool(
                config.config_loader.get("shell", "shell_mode", default=False)
            ),
            verbose = (
                bool(args.verbose)                                                   # -v flag set
                if args.prompt                                                       # single-turn: default off, -v enables
                else bool(config.config_loader.get("shell", "verbose", default=True))  # interactive: from ini
            ),
        )
