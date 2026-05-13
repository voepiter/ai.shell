# Changelog

All notable changes to ai.shell are documented here.

<!-- Entries are added by /changelog skill. Run: /changelog [v1.2.0] -->

## v0.1.5 — 2026-05-13

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
