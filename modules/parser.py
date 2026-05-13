"""CLI argument parser."""
import argparse
from .version import get_version
from .locale import t


def build() -> argparse.ArgumentParser:
    """Build and return the argparse parser with localised help strings."""
    parser = argparse.ArgumentParser(
        description=f"{t('parser','description')} v{get_version()}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=t('parser', 'examples'),
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {get_version()}")
    parser.add_argument("prompt", nargs="?",
                        help=t('parser', 'prompt_help'))
    parser.add_argument("-p", "--provider", dest="provider", metavar="NAME",
                        help=t('parser', 'provider_help'))
    parser.add_argument("-m", "--model", dest="model", metavar="NAME",
                        help=t('parser', 'model_help'))
    parser.add_argument("-i", "--instruction", dest="instruction", metavar="TEXT",
                        help=t('parser', 'instruction_help'))
    parser.add_argument("-l", "--language", dest="language", metavar="CODE",
                        help=t('parser', 'language_help'))
    parser.add_argument("-lm", "--list-models", dest="list_models", action="store_true",
                        help=t('parser', 'list_models_help'))
    parser.add_argument("-lp", "--list-providers", dest="list_providers", action="store_true",
                        help=t('parser', 'list_providers_help'))
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help=t('parser', 'verbose_help'))
    return parser
