"""Auto-update — once per day checks GitHub for a newer release and runs uv tool update."""
import re
import subprocess
from datetime import date
from pathlib import Path

import requests

from .version import get_version

_REPO          = "voepiter/ai.shell"
_API_URL       = f"https://api.github.com/repos/{_REPO}/releases/latest"
_CHANGELOG_URL = f"https://raw.githubusercontent.com/{_REPO}/main/CHANGELOG.md"
_CHECK_FILE    = ".update_check"


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


def _newer(latest: str, current: str) -> bool:
    """Return True if latest version tuple is greater than current."""
    def parse(v: str) -> tuple:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    try:
        return parse(latest) > parse(current)
    except (ValueError, AttributeError):
        return False


def _fetch_latest(timeout: int) -> str | None:
    """Fetch latest release tag from GitHub; return version string or None."""
    try:
        r = requests.get(_API_URL, timeout=timeout)
        r.raise_for_status()
        return r.json().get("tag_name", "").lstrip("v") or None
    except Exception:
        return None


def _changelog_section(version: str, timeout: int) -> str:
    """Fetch CHANGELOG.md from GitHub and return the section for version."""
    try:
        r = requests.get(_CHANGELOG_URL, timeout=timeout)
        r.raise_for_status()
        text = r.text
    except Exception:
        return ""
    m = re.search(rf"(## v{re.escape(version)}[^\n]*\n.*?)(?=\n## v|\Z)", text, re.S)
    return m.group(1).strip() if m else ""


def _run_update(latest: str, timeout: int) -> None:
    """Download and install latest release; print changelog if available."""
    current = get_version()
    print(f" update available: v{current} → v{latest}")
    print(" updating...", flush=True)
    result = subprocess.run(["uv", "tool", "update", "ai.shell"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f" update failed: {result.stderr.strip()}")
        return
    print(f" updated to v{latest}")
    section = _changelog_section(latest, timeout)
    if section:
        print()
        print(section)
        print()


def check_and_update(config_loader) -> None:
    """Check once per day for a newer release; update and show changelog if found."""
    if not config_loader.get("ui", "autoupdate", default=True):
        return

    check_path = _check_path(config_loader)
    if _checked_today(check_path):
        return

    timeout = config_loader.get_connection_timeout()
    print(" checking for updates...", flush=True)

    latest = _fetch_latest(timeout)
    _mark_checked(check_path)

    if not latest:
        return

    if not _newer(latest, get_version()):
        return

    _run_update(latest, timeout)


def force_update(config_loader) -> None:
    """Check for updates immediately, regardless of last-check date."""
    timeout = config_loader.get_connection_timeout()
    print(" checking for updates...", flush=True)
    latest = _fetch_latest(timeout)
    if not latest:
        print(" could not reach update server")
        return
    if not _newer(latest, get_version()):
        print(f" already up to date (v{get_version()})")
        return
    _run_update(latest, timeout)
