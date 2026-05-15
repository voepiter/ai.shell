#!/usr/bin/env python3
"""Entry point — parses args, routes to setup / single-turn / interactive chat."""

import sys

# backspace on multi-byte chars (Cyrillic, CJK) raises UnicodeDecodeError in strict mode
sys.stdin.reconfigure(encoding="utf-8", errors="replace")

try:
    import readline  # enables arrow-key navigation in input()
except ImportError:
    pass

from modules import parser, chat, single_turn, ui
from modules.locale import set_lang
from modules.state import AppState


def _early_lang() -> str | None:
    """Read language from -l argv or ai.ini [ui] language before parser is built."""
    argv = sys.argv[1:]
    for flag in ("-l", "--language"):
        if flag in argv:
            idx = argv.index(flag)
            if idx + 1 < len(argv):
                return argv[idx + 1]
    from modules.config import ConfigLoader
    return ConfigLoader().get("ui", "language", default=None)


def main():
    """Parse args, set locale early, dispatch to setup / single_turn / chat."""
    lang = _early_lang()
    if lang:
        set_lang(lang)
    args = parser.build().parse_args()

    from pathlib import Path
    from modules.config import _USER_CFG
    _here = Path(__file__).resolve().parent
    if not (_here / "ai.ini").exists() and not _USER_CFG.exists():
        from modules.setup import run as _setup
        _setup(lang=args.language)
        return

    try:
        state = AppState.from_args(args)
    except ValueError as e:
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

    lang = args.language or state.config.config_loader.get("ui", "language", default=None)
    if lang:
        set_lang(lang)

    from modules.config import migrate_config
    from modules.updates import check_and_update
    migrate_config(state.config.config_loader)
    check_and_update(state.config.config_loader)

    if args.telegram:
        from modules import telegram as _tg
        _tg.run(state)
    elif args.list_providers:
        ui.print_providers(state.config.config_loader)
    elif args.list_models:
        ui.print_models(state.config.provider, state.api_client, state.config.config_loader)
    elif args.prompt:
        from modules import skills as _skills
        prompt = args.prompt
        if prompt.startswith("/"):
            resolved = _skills.load(prompt, state.config.config_loader)
            if resolved is not None:
                prompt = resolved
        single_turn.run(state, prompt)
    else:
        if state.config.config_loader.get("telegram", "autostart", default=False):
            from modules import telegram as _tg
            _tg.start_thread(state)
            state.telegram = True
        chat.run(state)


if __name__ == "__main__":
    main()
