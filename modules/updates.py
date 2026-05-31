"""Auto-update — once per day runs uv tool upgrade; source remembered by uv."""
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from .version import get_version
from .config import ConfigLoader

_CHECK_FILE = ".update_check"

# True when running from an installed package (not a dev checkout)
_INSTALLED = "site-packages" in str(Path(__file__).parent.absolute())


# Return path to the last-check date file, stored next to ai.ini
def _check_path(config_loader: ConfigLoader) -> Path:
    return config_loader.config_path.parent / _CHECK_FILE


# Return True if the check file contains today's date
def _checked_today(path: Path) -> bool:
    try:
        return path.read_text().strip() == str(date.today())
    except Exception:
        return False


# Write today's date to the check file
def _mark_checked(path: Path) -> None:
    try:
        path.write_text(str(date.today()))
    except Exception:
        pass


# Run uv tool upgrade; restart process if a new version was installed
def _run_update() -> None:
    current = get_version()
    try:
        result = subprocess.run(
            ["uv", "tool", "upgrade", "ai.shell"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        print(" update skipped: uv not found in PATH")
        return
    if result.returncode != 0:
        print(f" update failed: {result.stderr.strip()}")
        return
    output = (result.stdout + result.stderr).strip()
    if "nothing to upgrade" in output.lower() or "already" in output.lower():
        print(f" already up to date (v{current})")
        return
    m = re.search(r'v[\d.]+\s*->\s*v([\d.]+)', output)
    new_ver = m.group(1) if m else "?"
    print(f" updating to v{new_ver} ...", flush=True)
    print(" restarting ...", flush=True)
    restart_args = [a for a in sys.argv if a not in ("-u", "--update")]
    os.execv(sys.argv[0], restart_args)


# Check once per day for updates; skip entirely in dev (non-installed) mode
def check_and_update(config_loader: ConfigLoader) -> None:
    if not _INSTALLED:
        return
    if not config_loader.get("ui", "autoupdate", default=True):
        return
    check_path = _check_path(config_loader)
    if _checked_today(check_path):
        return
    _mark_checked(check_path)
    print(" checking for updates...", flush=True)
    _run_update()


# Run update immediately, regardless of last-check date
def force_update(config_loader: ConfigLoader) -> None:
    print(" checking for updates...", flush=True)
    _run_update()
