"""Version resolution — installed package metadata or pyproject.toml fallback."""
import tomllib
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

def get_version() -> str:
    """Return version from installed package metadata or pyproject.toml fallback."""
    # Primary: read from installed package metadata
    try:
        return version("ai.shell")
    except PackageNotFoundError:
        pass
    # Fallback: read directly from pyproject.toml for dev installs
    try:
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        with pyproject.open("rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        return "unknown"
