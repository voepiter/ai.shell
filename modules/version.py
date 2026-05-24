"""Version resolution — installed package metadata or pyproject.toml fallback."""
import subprocess
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


# Return total git commit count as string, or None if git unavailable
def _git_count() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        count = result.stdout.strip()
        return count if count.isdigit() else None
    except Exception:
        return None


# Return (name, description) from pyproject.toml, with hardcoded fallbacks
def get_project_meta() -> tuple[str, str]:
    try:
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        with pyproject.open("rb") as f:
            proj = tomllib.load(f)["project"]
            return proj.get("name", "ai.shell"), proj.get("description", "")
    except Exception:
        return "ai.shell", ""


_BASE = "0.4"  # major.minor; patch = git commit count (dev) or baked by hatchling (release)


# Return version as major.minor.{git_commit_count}, falling back to package metadata
def get_version() -> str:
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
