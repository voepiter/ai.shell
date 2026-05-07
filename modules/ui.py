# Terminal rendering — stats, banners, model/provider lists
import sys
import requests
from . import text as ct
from . import colors as _col
from . import symbols as sym
from .api import APIFactory

_R = ct.resetcolor


def fmt_num(n: int | None) -> str:
    if n is None:
        return "?"
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def print_banner(provider: str, model: str, agent_name: str, shell_mode: bool):
    sh = f"{_col.model}on{_R}" if shell_mode else f"{_col.dim}off{_R}"
    
    print(f" {_col.marker}{sym.ai_marker}{_R} interactive chat mode")
    print(
        f"    {_col.dim}provider:{_R}{_col.provider}{provider}{_R}  "
        f"{_col.dim}model:{_R}{_col.model}{model}{_R}  "
        f"{_col.dim}agent:{_R}{_col.model}{agent_name}{_R}  "
        f"{_col.dim}shell:{_R}{sh}"
    )
    print(f"    {_col.command}/help{_R}{_col.dim} for commands  {sym.middle_dot}  Ctrl+C to exit{_R}")


def print_current_status(provider: str, model: str):
    print(
        f" {_col.dim}provider {sym.arrow}{_R} {_col.provider}{provider}{_R}  "
        f"{_col.dim}model {sym.arrow}{_R} {_col.model}{model}{_R}"
    )


def print_chat_help():
    print()
    print(f" {_col.dim}commands:{_R}")
    print(f"  {_col.command}/model{_R} {_col.dim}<name>{_R}         switch model")
    print(f"  {_col.command}/provider{_R} {_col.dim}<name>{_R}      switch provider  {_col.dim}(resets history){_R}")
    print(f"  {_col.command}/agent{_R} {_col.dim}<name>{_R}         switch agent / system prompt")
    print(f"  {_col.command}/shell{_R} {_col.dim}[on|off]{_R}       toggle shell agent mode")
    print(f"  {_col.command}/list-models, /lm{_R}     list models for current provider")
    print(f"  {_col.command}/list-providers, /lp{_R}  list all providers")
    print(f"  {_col.command}/quit{_R}                 exit chat")


def print_stats(
    token_in:      int | None,
    token_out:     int | None,
    elapsed:       float,
    total_in:      int | None = None,
    total_out:     int | None = None,
    total_elapsed: float | None = None,
):
    if token_in is None and token_out is None:
        return
    s = (
        f" {_col.dim}{sym.bullet}{_R}  "
        f"{_col.dim}tokens: in:{_R}{_col.model}{fmt_num(token_in)}{_R}  "
        f"{_col.dim}out:{_R}{_col.model}{fmt_num(token_out)}{_R}  "
        f"{_col.dim}time:{_R}{_col.model}{elapsed:.1f}{_R}s"
    )
    if total_in is not None and (total_in != token_in or total_out != token_out):
        s += (
            f"  {_col.dim}{sym.middle_dot}  total "
            f"in:{_R}{_col.model}{fmt_num(total_in)}{_R}  "
            f"{_col.dim}out:{_R}{_col.model}{fmt_num(total_out)}{_R}"
        )
        if total_elapsed is not None:
            s += f" time: {_col.model}{total_elapsed:.1f}{_R}s"
    print(s)


def print_chat_totals(total_in: int, total_out: int, total_elapsed: float = 0.0):
    if total_in or total_out:
        print(
            f"\n {_col.dim} {sym.bullet} session  "
            f"in:{_R}{_col.model}{fmt_num(total_in)}{_R}  "
            f"{_col.dim}out:{_R}{_col.model}{fmt_num(total_out)}{_R}  "
            f"{_col.dim}time:{_R}{_col.model}{total_elapsed:.1f}{_R}s"
        )
    print()


def print_providers(config_loader):
    print()
    print(f" {_col.dim}providers:{_R}")
    for name in APIFactory.list_providers():
        model   = config_loader.get_default_model(name) or ""
        env_var = APIFactory.API_KEY_ENV_VARS.get(name, "")
        print(
            f"  {_col.provider}{name:<12}{_R}"
            f"{_col.model}{model}{_R}  "
            f"{_col.dim}{env_var}{_R}"
        )


def print_models(provider: str, api_client, config_loader):
    default_model = config_loader.get_default_model(provider) or ""
    print(f"\n {_col.dim}provider:{_R} {_col.provider}{provider}{_R}")
    try:
        models = api_client.list_models()
    except NotImplementedError as e:
        print(f" {_col.error}{e}{_R}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f" {_col.error}error: {e}{_R}", file=sys.stderr)
        sys.exit(1)
    for entry in models:
        if isinstance(entry, tuple):
            mid, price = entry
            suffix = f"  {_col.dim}{price}{_R}" if price else ""
        else:
            mid, suffix = entry, ""
        marker = f"  {_col.dim}(default){_R}" if mid == default_model else ""
        print(f"  {_col.model if mid == default_model else ''}{mid}{_R}{marker}{suffix}")
