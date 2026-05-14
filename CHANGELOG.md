# Changelog

All notable changes to ai.shell are documented here.

## v0.3.61 — 2026-05-14

### Изменено
- Версия теперь включает счётчик git-коммитов как номер патча (`0.3.61`) — отображается в `-h` и баннере
- Символ ввода в чате заменён на `❯` светло-зелёного цвета; между ответом и следующим вводом добавлен горизонтальный разделитель
- Время в статистике теперь отображается в скобках `[1.4s]` без метки `time:`, весь блок одного dim-цвета

## v0.3.8 — 2026-05-14

### New
- Skills: define reusable slash-command prompts as Markdown files in `skills/<name>/<name>.md`; invoke with `/<name> [args]` in chat or `ai /<name> [args]` from the terminal
- `/skill` (no args) lists all available skills with descriptions
- Three built-in skills: `/code-review`, `/code-explain`, `/skill-creator` (interactive wizard that creates new skill files via the shell agent)
- `$ARGUMENTS` placeholder in skill files is substituted with whatever arguments the user passes

### Changed
- `--help` output is now fully localised: `usage:`, argument group titles, and `-h`/`-V` descriptions follow the active language

## v0.2.6 — 2026-05-13

### New
- Auto-update: once per day on startup, checks GitHub for a new release and runs `uv tool update ai.shell` if one is found; shows the relevant changelog section after updating
- Config migration: missing keys from `ai.ini.default` are automatically added to the user's `ai.ini` on startup — no manual edits needed after upgrades
- `autoupdate = true` key in `[ui]` section of `ai.ini`; set to `false` to disable

### Changed
- `pyproject.toml` now includes `[project.urls]` with the repository link

## v0.2.5 — 2026-05-13

### New
- First-run setup wizard: guides through provider selection, API keys, and UI preferences on first launch
- API keys are now stored in `ai.ini` — no more environment variables required
- Session logging: all conversations are saved; browse with `/sessions`, resume any session with `/resume <id>`
- Localization: Russian and English UI; set via `-l` flag, `/language` command, or `ai.ini`
- `/verbose` command and `-v` flag to toggle response details (token counts, timing)
- `/usage` command shows cumulative token usage for the current session
- Version number shown in `-h` output and interactive banner
- Daily log files in `log/` directory

### Fixed
- Shell mode: now correctly picks up commands wrapped in markdown fences (` ```bash `)
- Network errors in agentic loop are caught and reported instead of crashing
- Readline prompt boundaries fixed — backspace and arrow keys no longer overshoot the prompt
- First-run wizard now correctly detects config path when launched via symlink
- Session list showed wrong last prompt in some cases

### Changed
- Package renamed from `ai-shell` to `ai.shell`
- System instruction is now read from `ai.ini [system]` — no separate agent config
- Single-turn mode: clean output (response, then token stats) with no extra decorations
- Shell mode: command is always shown; verbose flag controls whether output is printed
- Log directory renamed from `.log` to `log`
