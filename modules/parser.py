# CLI argument parser
import argparse
from .version import get_version


def build() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Multi-model AI terminal assistant with a shell agent. v{get_version()}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  ai                                   interactive chat mode
  ai "prompt"                          single request
  ai -p openrouter --list-models       list models for provider
  ai -p openrouter -m gpt-5.3 "prompt" use specific provider/model
        """,
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {get_version()}")
    parser.add_argument("prompt", nargs="?",
                        help="prompt text (omit to enter chat mode)")
    parser.add_argument("-p", "--provider", dest="provider", metavar="NAME",
                        help="provider (google, openai, xai, deepseek, anthropic, openrouter)")
    parser.add_argument("-m", "--model", dest="model", metavar="NAME",
                        help="model name (default: from ai.ini [models])")
    parser.add_argument("-i", "--instruction", dest="instruction", metavar="TEXT",
                        help="system instruction (overrides ai.ini [system] instruction)")
    parser.add_argument("-l", "--language", dest="language", metavar="CODE",
                        help="language code: en, ru (overrides system locale)")
    parser.add_argument("-lm", "--list-models", dest="list_models", action="store_true",
                        help="list available models for selected provider and exit")
    parser.add_argument("-lp", "--list-providers", dest="list_providers", action="store_true",
                        help="list all supported providers and exit")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="show bash commands and output in agent mode (default: off)")
    return parser
