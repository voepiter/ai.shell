"""Version resolution — installed package metadata or pyproject.toml fallback."""
import tomllib
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

def get_version() -> str:
    """Return version from installed package metadata or pyproject.toml fallback."""
    try:
        return version("ai.shell")
    except PackageNotFoundError:
        pass
    try:
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        with pyproject.open("rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        return "unknown"
