"""Skill loader — discovers and loads .md skill files from skill directories."""
from pathlib import Path
from .config import ConfigLoader

# Bundled skills shipped with the package
_PKG_SKILLS = Path(__file__).parent.parent / "skills"


# Return skill search paths: user config dir first, then bundled package skills
def _dirs(config_loader: ConfigLoader) -> list[Path]:
    user_dir = (config_loader.config_path.parent / "skills").resolve()
    paths = [user_dir]
    if _PKG_SKILLS.resolve() != user_dir:
        paths.append(_PKG_SKILLS)
    return paths


# Return path to skills/name/name.md or None if not found
def _find(name: str, config_loader: ConfigLoader) -> Path | None:
    for d in _dirs(config_loader):
        p = d / name / f"{name}.md"
        if p.exists():
            return p
    return None


# Strip YAML frontmatter, substitute $ARGUMENTS; return (content, description)
def _parse(path: Path, args: str) -> tuple[str, str]:
    raw = path.read_text(encoding="utf-8")
    description = ""
    if raw.startswith("---"):
        end = raw.find("---", 3)
        if end != -1:
            for line in raw[3:end].splitlines():
                if line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
            raw = raw[end + 3:].lstrip()
    return raw.replace("$ARGUMENTS", args).strip(), description


# Parse /name [args] input; return skill content with $ARGUMENTS substituted, or None
def load(raw_input: str, config_loader: ConfigLoader) -> str | None:
    parts = raw_input.lstrip("/").split(maxsplit=1)
    name  = parts[0].lower()
    if not name:
        return None
    args  = parts[1] if len(parts) > 1 else ""
    path  = _find(name, config_loader)
    if path is None:
        return None
    content, _ = _parse(path, args)
    return content


# Return sorted (name, description) pairs for all available skills
def list_skills(config_loader: ConfigLoader) -> list[tuple[str, str]]:
    seen:   set[str]              = set()
    result: list[tuple[str, str]] = []
    for d in _dirs(config_loader):
        if not d.exists():
            continue
        for skill_dir in sorted(d.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name in seen:
                continue
            md = skill_dir / f"{skill_dir.name}.md"
            if md.exists():
                _, desc = _parse(md, "")
                result.append((skill_dir.name, desc))
                seen.add(skill_dir.name)
    return result
