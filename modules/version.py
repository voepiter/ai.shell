import tomllib
from pathlib import Path

def get_version() -> str:
    try:
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        with pyproject.open("rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        return "unknown"
