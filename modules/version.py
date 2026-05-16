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


_BASE = "0.4"  # major.minor; patch = git commit count (dev) or baked by hatchling (release)


def get_version() -> str:
    """Return version as major.minor.{git_commit_count}, falling back to package metadata."""
    # Dev build: .git present → base + git commit count as patch
    if (Path(__file__).parent.parent / ".git").exists():
        count = _git_count()
        return f"{_BASE}.{count}" if count else _BASE
    # Installed package: use exact version baked in at build time
    try:
        return version("ai.shell")
    except PackageNotFoundError:
        return _BASE


__version__ = get_version()
