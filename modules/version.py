"""Version resolution — installed package metadata or pyproject.toml fallback."""
import subprocess
import tomllib
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path


def _base(v: str) -> str:
    # Return major.minor from a version string
    parts = v.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else v


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
    # Resolve base version from installed metadata or pyproject.toml
    base = None
    try:
        base = _base(version("ai.shell"))
    except PackageNotFoundError:
        pass
    if base is None:
        try:
            pyproject = Path(__file__).parent.parent / "pyproject.toml"
            with pyproject.open("rb") as f:
                base = _base(tomllib.load(f)["project"]["version"])
        except Exception:
            pass
    if base is None:
        return "unknown"
    # Replace patch with git commit count when available
    count = _git_count()
    return f"{base}.{count}" if count else base
