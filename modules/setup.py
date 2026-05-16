"""First-run setup wizard — creates ai.ini from ai.ini.default."""
import locale
import os
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

_BASE      = Path(__file__).parent.parent
_EXAMPLE   = _BASE / "ai.ini.default"
_LOCALES   = _BASE / "locales"
_installed = "site-packages" in str(_BASE)
_CONFIG    = (Path.home() / ".config" / "ai-shell" / "ai.ini"
              if _installed else _BASE / "ai.ini")

# Provider name → (env var name, api key url)
_PROVIDERS = {
    "google":     ("GEMINI_API_KEY",     "https://aistudio.google.com/apikey"),
    "openai":     ("OPENAI_API_KEY",     "https://platform.openai.com/api-keys"),
    "xai":        ("XAI_API_KEY",        "https://console.x.ai"),
    "deepseek":   ("DEEPSEEK_API_KEY",   "https://platform.deepseek.com"),
    "anthropic":  ("ANTHROPIC_API_KEY",  "https://console.anthropic.com"),
    "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/keys"),
}


# Detect system language from env vars, fall back to "en"
def _detect_lang() -> str:
    for var in ("LANGUAGE", "LANG", "LC_ALL", "LC_MESSAGES"):
        val = os.environ.get(var, "")
        if val:
            code = val.split("_")[0].split(".")[0].lower()
            if code and code not in ("c", "posix"):
                return code
    try:
        loc = locale.getdefaultlocale()[0] or ""
        if loc:
            return loc.split("_")[0].lower()
    except Exception:
        pass
    return "en"


# Load locale TOML file; fall back to "en" if requested lang is missing
def _load_strings(lang: str) -> dict:
    for code in (lang, "en"):
        path = _LOCALES / f"{code}.toml"
        if path.exists():
            with open(path, "rb") as f:
                return tomllib.load(f)
    return {}


# Look up a translated string by nested key path and format with kwargs
def _s(strings: dict, *keys: str, **fmt) -> str:
    val = strings
    for k in keys:
        if not isinstance(val, dict):
            return ""
        val = val.get(k, "")
    s = val if isinstance(val, str) else ""
    return s.format(**fmt) if fmt else s


# Prompt for text input; return default on empty or interrupt
def _ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        return input(f"{prompt}{hint}: ").strip() or default
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


# Prompt for yes/no; return default on empty or interrupt
def _yn(prompt: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    try:
        ans = input(f"{prompt} [{hint}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return default if not ans else ans.startswith("y")


# Step 1: ask whether the terminal supports unicode symbols
def _step_unicode(s: dict) -> bool:
    print(_s(s, "wizard", "step1"))
    print()
    ok = _yn(_s(s, "wizard", "step1_question"), default=True)
    if not ok:
        print(_s(s, "wizard", "step1_no"))
    return ok


# Step 2: collect API keys for each provider; skip those already in env
def _step_keys(s: dict) -> dict:
    print(_s(s, "wizard", "step2"))
    collected = {}
    for provider, (env_var, url) in _PROVIDERS.items():
        print()
        if os.environ.get(env_var):
            print(f"  {env_var}: {_s(s, 'wizard', 'step2_from_env')}")
            continue
        print(f"  [ {provider} ]  {url}")
        val = _ask(f"  {env_var}", default="")
        if val:
            collected[env_var] = val
    return collected


# Step 3: choose the default provider from those that have a key configured
def _step_settings(s: dict, keys: dict) -> str:
    print(_s(s, "wizard", "step3"))
    available = [
        p for p, (env_var, _) in _PROVIDERS.items()
        if os.environ.get(env_var) or env_var in keys
    ]
    if available:
        print(_s(s, "wizard", "step3_available", providers=", ".join(available)))
    else:
        print(_s(s, "wizard", "step3_none"))
    default = available[0] if available else "google"
    print()
    chosen = _ask(_s(s, "wizard", "step3_question"), default=default)
    if chosen not in _PROVIDERS:
        chosen = default
    return chosen


# Write ai.ini by patching the default template line-by-line
def _write_config(keys: dict, provider: str, unicode_ok: bool):
    if not _EXAMPLE.exists():
        raise FileNotFoundError(f"Template not found: {_EXAMPLE}")

    with open(_EXAMPLE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    out = []
    in_api_keys  = False
    in_providers = False

    for line in lines:
        stripped = line.strip()

        # Track which section we're in
        if stripped.startswith("["):
            section     = stripped.strip("[]")
            in_api_keys  = section == "api_keys"
            in_providers = section == "providers"

        # Rewrite [api_keys] values with collected keys
        if in_api_keys and "=" in stripped and not stripped.startswith("#"):
            env_var = stripped.split("=")[0].strip()
            val = keys.get(env_var, "")
            out.append(f'{env_var:<19}= "{val}"\n')
            continue

        # Rewrite default provider
        if in_providers and stripped.startswith("default") and "=" in stripped and not stripped.startswith("#"):
            out.append(f'default = "{provider}"\n')
            continue

        # Rewrite unicode flag, preserve inline comment if present
        if "unicode" in line and "=" in line and not stripped.startswith("#"):
            flag    = "true" if unicode_ok else "false"
            eq      = line.index("=")
            comment = ""
            rest    = line[eq + 1:]
            if "#" in rest:
                comment = "  " + rest[rest.index("#"):].rstrip()
            out.append(line[:eq + 1] + f" {flag}{comment}\n")
            continue

        out.append(line)

    _CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG, "w", encoding="utf-8") as f:
        f.writelines(out)
    _CONFIG.chmod(0o600)


# Entry point for the setup wizard — called by main() on first run
def run(lang: str | None = None):
    lang = lang or _detect_lang()
    s    = _load_strings(lang)

    unicode_ok = _step_unicode(s)
    keys       = _step_keys(s)
    provider   = _step_settings(s, keys)

    _write_config(keys, provider, unicode_ok)

    print()
    print(_s(s, "wizard", "done", path=str(_CONFIG)))
    print(_s(s, "wizard", "restart"))
    print()
