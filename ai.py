#!/usr/bin/env python3
# AI shell chat — entry point
# Usage: ai "your question"  |  ai  (interactive)
# API keys: GOOGLE_API_KEY, OPENAI_API_KEY, XAI_API_KEY, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY

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


def main():
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

    if args.list_providers:
        ui.print_providers(state.config.config_loader)
    elif args.list_models:
        ui.print_models(state.config.provider, state.api_client, state.config.config_loader)
    elif args.prompt:
        single_turn.run(state, args.prompt)
    else:
        chat.run(state)


if __name__ == "__main__":
    main()
