# Terminal rendering — stats, banners, model/provider lists
import sys
import requests
from . import text as ct
from . import colors as _col
from . import symbols as sym
from .api import APIFactory
from .locale import t

_R = ct.resetcolor


def fmt_num(n: int | None) -> str:
    if n is None:
        return "?"
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def print_banner(provider: str, model: str, shell_mode: bool):
    sh = f"{_col.model}on{_R}" if shell_mode else f"{_col.dim}off{_R}"

    print(f" {_col.marker}{sym.ai_marker}{_R} {t('ui','interactive_chat')}")
    print(
        f"    {_col.dim}{t('ui','provider_label')}{_R}{_col.provider}{provider}{_R}  "
        f"{_col.dim}{t('ui','model_label')}{_R}{_col.model}{model}{_R}  "
        f"{_col.dim}{t('ui','shell_label')}{_R}{sh}"
    )
    print(f"    {_col.command}/help{_R}{_col.dim} {t('ui','help_for_cmds')}  {sym.middle_dot}  {t('ui','ctrl_c_exit')}{_R}")


def print_current_status(provider: str, model: str):
    print(
        f" {_col.dim}provider {sym.arrow}{_R} {_col.provider}{provider}{_R}  "
        f"{_col.dim}model {sym.arrow}{_R} {_col.model}{model}{_R}"
    )


def print_chat_help():
    print()
    print(f" {_col.dim}{t('ui','commands_header')}{_R}")
    print(f"  {_col.command}/model{_R} {_col.dim}<name>{_R}         {t('ui','help_model')}")
    print(f"  {_col.command}/provider{_R} {_col.dim}<name>{_R}      {t('ui','help_provider')}  {_col.dim}{t('ui','resets_history')}{_R}")
    print(f"  {_col.command}/shell{_R} {_col.dim}[on|off]{_R}       {t('ui','help_shell')}")
    print(f"  {_col.command}/list-models, /lm{_R}     {t('ui','help_list_models')}")
    print(f"  {_col.command}/list-providers, /lp{_R}  {t('ui','help_list_providers')}")
    print(f"  {_col.command}/language{_R} {_col.dim}<code>{_R}      {t('ui','help_language')}")
    print(f"  {_col.command}/usage{_R}                {t('ui','help_usage')}")
    print(f"  {_col.command}/clear{_R}                {t('ui','help_clear')}")
    print(f"  {_col.command}/quit{_R}                 {t('ui','help_quit')}")


def print_stats(
    token_in:    int | None,
    token_out:   int | None,
    elapsed:     float,
    request_num: int | None = None,
):
    if token_in is None and token_out is None:
        return
    req = f"{_col.dim}{t('ui','tok_request')}{request_num}  " if request_num is not None else ""
    s = (
        f" {_col.dim}{sym.bullet}{_R}  "
        f"{req}"
        f"{_col.dim}{t('ui','tok_tokens')} {t('ui','tok_in')}{fmt_num(token_in)}  "
        f"{t('ui','tok_out')}{fmt_num(token_out)}  "
        f"{t('ui','tok_time')}{elapsed:.1f}{_R}s"
    )
    print(s)


def print_usage(total_in: int, total_out: int, total_elapsed: float):
    if not total_in and not total_out:
        print(f" {_col.dim}—{_R}")
        return
    print(
        f" {_col.dim}{sym.bullet} {t('ui','tok_session')}  "
        f"{t('ui','tok_in')}{fmt_num(total_in)}  "
        f"{t('ui','tok_out')}{fmt_num(total_out)}  "
        f"{t('ui','tok_time')}{total_elapsed:.1f}s{_R}"
    )


def print_chat_totals(total_in: int, total_out: int, total_elapsed: float = 0.0):
    print()
    print_usage(total_in, total_out, total_elapsed)
    print()


def print_providers(config_loader):
    print()
    print(f" {_col.dim}{t('ui','providers_header')}{_R}")
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
    print(f"\n {_col.dim}{t('ui','provider_label')}{_R} {_col.provider}{provider}{_R}")
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
        marker = f"  {_col.dim}{t('ui','default_marker')}{_R}" if mid == default_model else ""
        print(f"  {_col.model if mid == default_model else ''}{mid}{_R}{marker}{suffix}")
