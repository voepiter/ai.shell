"""Auto-update — once per day runs uv tool upgrade; source remembered by uv."""
import subprocess
from datetime import date
from pathlib import Path

from .version import get_version

_CHECK_FILE = ".update_check"


def _check_path(config_loader) -> Path:
    """Return path to the last-check date file, stored next to ai.ini."""
    return config_loader.config_path.parent / _CHECK_FILE


def _checked_today(path: Path) -> bool:
    """Return True if the check file contains today's date."""
    try:
        return path.read_text().strip() == str(date.today())
    except Exception:
        return False


def _mark_checked(path: Path) -> None:
    """Write today's date to the check file."""
    try:
        path.write_text(str(date.today()))
    except Exception:
        pass


def _run_update() -> None:
    """Run uv tool upgrade and report result."""
    current = get_version()
    print(" updating...", flush=True)
    result = subprocess.run(["uv", "tool", "upgrade", "ai.shell"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f" update failed: {result.stderr.strip()}")
        return
    # uv prints "Updated ai.shell vX -> vY" or "Nothing to upgrade"
    output = (result.stdout + result.stderr).strip()
    if "nothing to upgrade" in output.lower() or "already" in output.lower():
        print(f" already up to date (v{current})")
    else:
        print(f" updated — restart to apply")


def check_and_update(config_loader) -> None:
    """Check once per day for updates via uv tool upgrade."""
    if not config_loader.get("ui", "autoupdate", default=True):
        return
    check_path = _check_path(config_loader)
    if _checked_today(check_path):
        return
    _mark_checked(check_path)
    print(" checking for updates...", flush=True)
    _run_update()


def force_update(config_loader) -> None:
    """Run update immediately, regardless of last-check date."""
    print(" checking for updates...", flush=True)
    _run_update()
