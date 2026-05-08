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
from modules.state import AppState


def main():
    args = parser.build().parse_args()

    if args.language:
        from modules.locale import set_lang
        set_lang(args.language)

    from pathlib import Path
    if not (Path(__file__).resolve().parent / "ai.ini").exists():
        from modules.setup import run as _setup
        _setup(lang=args.language)
        return

    try:
        state = AppState.from_args(args)
    except ValueError as e:
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

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
