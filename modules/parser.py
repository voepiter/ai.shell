"""CLI argument parser."""
import argparse
import sys
from .version import get_version
from .locale import t


# Custom action: print locale help block and exit
class _HelpAction(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=None):
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        from . import ui
        ui.print_startup_line()
        print(t('parser', 'full_help').format(version=get_version()))
        sys.exit(0)


def build() -> argparse.ArgumentParser:
    """Build and return the argparse parser with localised help strings."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-h", "--help", action=_HelpAction)
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("-p", "--provider", dest="provider", metavar="NAME")
    parser.add_argument("-m", "--model", dest="model", metavar="NAME")
    parser.add_argument("-i", "--instruction", dest="instruction", metavar="TEXT")
    parser.add_argument("-l", "--language", dest="language", metavar="CODE")
    parser.add_argument("-lm", "--list-models", dest="list_models", action="store_true")
    parser.add_argument("-lp", "--list-providers", dest="list_providers", action="store_true")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")
    parser.add_argument("-t", "--telegram", dest="telegram", action="store_true")
    parser.add_argument("-s", "--skills", dest="skills", action="store_true")
    parser.add_argument("-u", "--update", dest="update", action="store_true")
    return parser
