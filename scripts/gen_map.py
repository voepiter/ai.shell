#!/usr/bin/env python3
"""Regenerate MAP.md from module docstrings and function signatures."""
import ast
from pathlib import Path

ROOT = Path(__file__).parent.parent

_STATIC = """\
## Common tasks

| Task | File | Line |
|------|------|------|
| Add slash command | modules/commands.py | 30 |
| Add autocomplete entry | modules/completer.py | 12 |
| Add locale string | locales/en.toml + ru.toml | [common] / [commands] |
| Add CLI flag | modules/parser.py | 1 |
| Add provider | providers/ + api.py | new file |
| Change banner/stats UI | modules/ui.py | 1 |
| Change update logic | modules/updates.py | 1 |
| Change agent loop | modules/agent.py | 1 |

## Config keys (ai.ini sections)

| Section | Key | Description |
|---------|-----|-------------|
| ui | unicode | Unicode symbols vs ASCII fallback |
| ui | autoupdate | Auto-check PyPI once per day |
| ui | language | Override locale (en / ru) |
| models | \\<provider\\> | Default model per provider |
| system | instruction | System prompt override |
| telegram | token | Bot token |
| telegram | allowed_ids | Allowed usernames (comma-sep) |
| connection | timeout | HTTP timeout in seconds |

## Env vars → provider key mapping

| Env var | Provider |
|---------|----------|
| ANTHROPIC_API_KEY | anthropic |
| OPENAI_API_KEY | openai |
| OPENROUTER_API_KEY | openrouter |
| DEEPSEEK_API_KEY | deepseek |
| XAI_API_KEY | xai |
| GOOGLE_API_KEY | google |

## Config & data files

locales/en.toml  English UI strings — [unicode][keys][settings][ui][common][commands][parser][agent]
locales/ru.toml  Russian UI strings — same sections as en.toml
ai.ini.default   Template / reference config
pyproject.toml   Package build config (name=ai.shell, entry point: ai=ai:main)\
"""


def _first_line(s: str) -> str:
    return s.strip().splitlines()[0] if s else ""


def _sig_args(node: ast.FunctionDef) -> str:
    args = []
    for a in node.args.args:
        if a.arg not in ("self", "cls"):
            args.append(a.arg)
    if node.args.vararg:
        args.append(f"*{node.args.vararg.arg}")
    if node.args.kwarg:
        args.append(f"**{node.args.kwarg.arg}")
    return ", ".join(args)


def parse_file(path: Path) -> dict:
    """Return {lines, doc, symbols} extracted via ast."""
    source = path.read_text(encoding="utf-8", errors="replace")
    lines = len(source.splitlines())
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"lines": lines, "doc": "", "symbols": []}

    doc = _first_line(ast.get_docstring(tree) or "")
    symbols = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fdoc = _first_line(ast.get_docstring(node) or "")
            if fdoc:
                symbols.append((node.name, _sig_args(node), fdoc))
        elif isinstance(node, ast.ClassDef):
            cdoc = _first_line(ast.get_docstring(node) or "")
            if cdoc:
                symbols.append((node.name, "", cdoc))
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith("__"):
                        continue
                    mdoc = _first_line(ast.get_docstring(item) or "")
                    if mdoc:
                        symbols.append((f"{node.name}.{item.name}", _sig_args(item), mdoc))

    return {"lines": lines, "doc": doc, "symbols": symbols}


def fmt_entry(name: str, info: dict) -> str:
    """Format one file entry: header line + tab-indented symbols."""
    doc_part = f"  {info['doc']}" if info["doc"] else ""
    rows = [f"{name}  {info['lines']}{doc_part}"]
    for sym_name, args, sym_doc in info["symbols"]:
        sig = f"{sym_name}({args})" if args else sym_name
        rows.append(f"\t{sig}  {sym_doc}")
    return "\n".join(rows)


def build_section(title: str, paths: list) -> str:
    """Build one ## section from a list of .py paths."""
    entries = [fmt_entry(p.name, parse_file(p)) for p in sorted(paths)]
    return f"## {title}\n\n" + "\n\n".join(entries)


def main():
    """Write MAP.md to project root."""
    modules = [
        p for p in sorted((ROOT / "modules").glob("*.py"))
        if p.name != "__init__.py"
    ]
    providers = [
        p for p in sorted((ROOT / "providers").glob("*.py"))
        if p.name != "__init__.py"
    ]

    parts = [
        "# Project Map\n\nMulti-model LLM CLI client + bash agent.",
        build_section("Entry Point", [ROOT / "ai.py"]),
        build_section("modules/", modules),
        build_section("providers/", providers),
        _STATIC,
    ]

    (ROOT / "MAP.md").write_text("\n\n---\n\n".join(parts) + "\n", encoding="utf-8")
    print("MAP.md updated")


if __name__ == "__main__":
    main()
