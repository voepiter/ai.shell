# Project Map

Multi-model LLM CLI client + bash agent.

## Entry Point

| File | Lines | Role |
|------|-------|------|
| `ai.py` | 68 | Entry point — parses args, routes to setup / single-turn / chat |

`_early_lang()` — reads `-l` argv or `ai.ini [ui] language` before `parser.build()` so `-h` output is already localised  
`main()` — dispatches: setup wizard → `modules/setup`, single-turn → `modules/single_turn`, interactive chat → `modules/chat`

---

## modules/

### Core flow

| File | Lines | Key symbols |
|------|-------|-------------|
| `state.py` | 37 | `AppState` — shared runtime state (provider, model, history, flags) |
| `parser.py` | 30 | `build()` → `argparse.ArgumentParser`; all help strings via `t('parser',...)` |
| `config.py` | 78 | `ConfigLoader` — reads ai.ini; `Config` — typed config object |
| `api.py` | 64 | `APIFactory` — instantiates the right provider client from config |
| `chat.py` | 107 | `run(state)` — interactive REPL loop |
| `single_turn.py` | 61 | `run(state, prompt)` — one-shot prompt then exit |
| `agent.py` | 123 | `agentic_loop(..., verbose)` — bash agent loop; `build_system_instruction(...)` |
| `commands.py` | 180 | `handle(raw, history, state)` — slash-command dispatcher (`/help`, `/clear`, `/model`, `/verbose`, `/sessions`, `/resume`, …); `_cmd_sessions(log_dir)`, `_cmd_resume(session_id, history, log_dir)` |
| `shell.py` | 63 | `CommandResult`; `extract_commands(text)`, `is_dangerous(cmd, patterns)`, `run_command(cmd, timeout)` |

### UI / display

| File | Lines | Key symbols |
|------|-------|-------------|
| `ui.py` | 126 | `print_banner`, `print_chat_help`, `print_stats`, `print_chat_totals`, `print_models`, `print_providers`, `print_current_status`, `fmt_num` |
| `spinner.py` | 51 | `Spinner` — animated terminal spinner (context manager) |
| `logo.py` | 50 | `print_logo(path, delay, logo_gradient)` — RGB gradient logo renderer |
| `text.py` | 66 | `forecolor`, `backcolor`, `highlight` — ANSI helpers |
| `colors.py` | 25 | `_fg(n)`, `_bg(n)` — low-level 256-color ANSI codes |
| `symbols.py` | 18 | `_u(uni, asc)` — Unicode/ASCII symbol picker |

### Utilities

| File | Lines | Key symbols |
|------|-------|-------------|
| `logger.py` | 38 | `Logger` — per-session JSONL logger (`log/YYYYMMDD_HHMMSS.jsonl`); `log_user()`, `log_assistant()`, `session_id` |
| `counter.py` | 3  | `RequestCounter` — in-memory request counter, starts at 1 per session |
| `locale.py` | 62 | `t(*keys, **fmt)` — translated string lookup; `set_lang(code)` — runtime switch; auto-detects system lang on import |
| `version.py` | 9  | `get_version()` — reads version from `pyproject.toml` |
| `setup.py` | 202 | `run()` — first-run interactive setup wizard; helpers: `_detect_lang`, `_ask`, `_yn`, `_step_unicode`, `_step_keys`, `_step_settings`, `_write_config` |

---

## providers/

All clients stream responses and return token usage.

| File | Lines | Class | Backend |
|------|-------|-------|---------|
| `base.py` | 99 | `BaseAPIClient` (ABC), `APIError` | — |
| `anthropic.py` | 60 | `AnthropicClient(BaseAPIClient)` | Anthropic API |
| `openai.py` | 58 | `OpenAIClient(BaseAPIClient)` | OpenAI API |
| `openrouter.py` | 55 | `OpenRouterClient(OpenAIClient)` | OpenRouter (OpenAI-compat) |
| `deepseek.py` | 42 | `DeepSeekClient(BaseAPIClient)` | DeepSeek API |
| `google.py` | 55 | `GoogleClient(BaseAPIClient)` | Google Gemini |
| `xai.py` | 42 | `XAIClient(BaseAPIClient)` | xAI Grok |

---

## Config & data files

| File | Purpose |
|------|---------|
| `ai.ini` | Active user config (provider, model, keys, flags) |
| `ai.ini.default` | Template / reference config |
| `logo.ascii` | ASCII art shown at startup |
| `locales/en.toml` | English UI strings — sections: `[unicode]` `[keys]` `[settings]` `[ui]` `[common]` `[commands]` `[parser]` `[agent]` |
| `locales/ru.toml` | Russian UI strings — same sections as en.toml |
| `requirements.txt` | Python dependencies |
| `pyproject.toml` | Build config for `uv tool install git+...` |

---

## Data flow

```
ai.py main()
  ├─ setup wizard ──────────────────────────► modules/setup.py
  ├─ single-turn: modules/single_turn.run()
  │     └─ APIFactory → provider.stream() → print
  └─ chat: modules/chat.run()
        ├─ commands.handle()   (slash commands)
        └─ agentic_loop()      (bash agent, when --shell)
              └─ shell.run_command() → back to API
```
