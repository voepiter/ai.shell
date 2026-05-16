"""Version resolution — installed package metadata or pyproject.toml fallback."""
import subprocess
import tomllib
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path



def _git_count() -> str | None:
    # Return total git commit count as string, or None if git unavailable
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        count = result.stdout.strip()
        return count if count.isdigit() else None
    except Exception:
        return None


def get_project_meta() -> tuple[str, str]:
    """Return (name, description) from pyproject.toml, with hardcoded fallbacks."""
    try:
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        with pyproject.open("rb") as f:
            proj = tomllib.load(f)["project"]
            return proj.get("name", "ai.shell"), proj.get("description", "")
    except Exception:
        return "ai.shell", ""


def get_version() -> str:
    """Return version as major.minor.{git_commit_count}, falling back to package metadata."""
    # Use full installed version if it already has a patch component
    raw = None
    try:
        raw = version("ai.shell")
    except PackageNotFoundError:
        pass
    if raw is None:
        try:
            pyproject = Path(__file__).parent.parent / "pyproject.toml"
            with pyproject.open("rb") as f:
                raw = tomllib.load(f)["project"]["version"]
        except Exception:
            pass
    if raw is None:
        return "unknown"
    # If version already has 3+ parts (real release), use as-is
    if len(raw.split(".")) >= 3:
        return raw
    # Dev build: append git commit count as patch
    count = _git_count()
    return f"{raw}.{count}" if count else raw
