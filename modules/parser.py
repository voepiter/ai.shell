# CLI argument parser
import argparse


def build() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="shell tool for interacting with various LLM APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  ai "your question"               single-turn request
  ai                               enter interactive chat mode
  ai -p openai -m gpt-5.3 "..."    use specific provider/model
  ai --list-models
  ai -p openai --list-models
  ai --list-providers
        """,
    )
    parser.add_argument("prompt", nargs="?",
                        help="prompt text (omit to enter chat mode)")
    parser.add_argument("-p", "--provider", dest="provider", metavar="NAME",
                        help="provider (google, openai, xai, deepseek, anthropic, openrouter)")
    parser.add_argument("-m", "--model", dest="model", metavar="NAME",
                        help="model name (default: from ai.ini [models])")
    parser.add_argument("-i", "--instruction", dest="instruction", metavar="TEXT",
                        help="system instruction (overrides ai.ini [system] instruction)")
    parser.add_argument("-lm", "--list-models", dest="list_models", action="store_true",
                        help="list available models for selected provider and exit")
    parser.add_argument("-lp", "--list-providers", dest="list_providers", action="store_true",
                        help="list all supported providers and exit")
    return parser
