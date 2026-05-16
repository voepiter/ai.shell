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
    project_root = Path(__file__).parent.parent
    # Dev build: .git present → pyproject base + git commit count as patch
    if (project_root / ".git").exists():
        try:
            with (project_root / "pyproject.toml").open("rb") as f:
                raw = tomllib.load(f)["project"]["version"]
            parts = raw.split(".")
            base = ".".join(parts[:2]) if len(parts) >= 2 else raw
            count = _git_count()
            return f"{base}.{count}" if count else base
        except Exception:
            pass
    # Installed package: use exact version from metadata
    try:
        return version("ai.shell")
    except PackageNotFoundError:
        pass
    return "unknown"
