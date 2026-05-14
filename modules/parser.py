"""CLI argument parser."""
import argparse
from .version import get_version
from .locale import t


# Formatter that replaces hardcoded English "usage:" prefix with a localised string
class _LocalizedFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = t('parser', 'usage_label') + ': '
        return super()._format_usage(usage, actions, groups, prefix)


def build() -> argparse.ArgumentParser:
    """Build and return the argparse parser with localised help strings."""
    parser = argparse.ArgumentParser(
        description=f"{t('parser','description')} v{get_version()}",
        formatter_class=_LocalizedFormatter,
        epilog=t('parser', 'examples'),
        add_help=False,
    )
    parser._positionals.title = t('parser', 'positionals_title')
    parser._optionals.title   = t('parser', 'options_title')
    # Help and version flags (added manually to allow localised help strings)
    parser.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS,
                        help=t('parser', 'help_help'))
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {get_version()}",
                        help=t('parser', 'version_help'))
    # Positional prompt — omit to enter interactive mode
    parser.add_argument("prompt", nargs="?",
                        help=t('parser', 'prompt_help'))
    # Provider / model selection
    parser.add_argument("-p", "--provider", dest="provider", metavar="NAME",
                        help=t('parser', 'provider_help'))
    parser.add_argument("-m", "--model", dest="model", metavar="NAME",
                        help=t('parser', 'model_help'))
    # Session overrides
    parser.add_argument("-i", "--instruction", dest="instruction", metavar="TEXT",
                        help=t('parser', 'instruction_help'))
    parser.add_argument("-l", "--language", dest="language", metavar="CODE",
                        help=t('parser', 'language_help'))
    # Listing flags
    parser.add_argument("-lm", "--list-models", dest="list_models", action="store_true",
                        help=t('parser', 'list_models_help'))
    parser.add_argument("-lp", "--list-providers", dest="list_providers", action="store_true",
                        help=t('parser', 'list_providers_help'))
    # Agent mode flag
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help=t('parser', 'verbose_help'))
    return parser
