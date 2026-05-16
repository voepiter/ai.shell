![AI.SHELL](ai.shell.jpg)

AI terminal interface agent. can run shell commands, telegram bot.
Supports multiple LLM: OpenRouter, DeepSeek, OpenAI ChatGPT, Anthropic Claude, Google Gemini, XAI Grok.
Requires [API keys](##api-keys)

## Installation

Recommended via the [UV package manager](https://github.com/astral-sh/uv)

```bash
uv tool install git+https://github.com/voepiter/ai.shell.git
```

## Configuration

The `ai.ini` file is created on first run by a setup wizard. Default settings come from `ai.ini.default`.

## Usage

```bash
# Interactive mode with bash agent
ai

# Single-turn query
ai "your question"

# Select provider and model
ai -p openai -m gpt-5.3-mini "your question"

# List providers
ai -lp
# List models
ai -p openrouter -lm
```

## Command-line Options

| Option                    | Description                  |
|---------------------------|------------------------------|
| `"prompt"`                | Query text for the AI        |
| `-h` / `--help`           | Show help                    |
| `-l` / `--language`       | Select language              |
| `-i` / `--instruction`    | System instruction           |
| `-p` / `--provider`       | Provider                     |
| `-m` / `--model`          | Model name                   |
| `-lp`/ `--list-providers` | List available providers     |
| `-lm`/ `--list-models`    | List available models        |
| `-v` / `--verbose`        | Show bash commands output in agent mode |
| `-t` / `--telegram`       | Start Telegram bot polling loop |                                                       |

## Verbose Mode

Controls whether intermediate bash commands output are shown during agent execution. The final answer is always displayed.

| Mode          | Default | How to change                          |
|---------------|---------|----------------------------------------|
| Interactive   | `true`  | Set `verbose = true/false` in `ai.ini` `[shell]`, or toggle with `/verbose` |
| Single-turn   | `false` | Pass `-v` / `--verbose` flag           |

```bash
# Single-turn with verbose output
ai -v "show disk usage"
```

## Session Management

Each interactive session is saved as a JSONL file in `~/.local/share/ai-shell/log/` (or `log/` when running from source).

| Command                   | Description                                        |
|---------------------------|----------------------------------------------------|
| `/sessions`               | List the 10 most recent sessions with last prompt  |
| `/resume <session_id>`    | Load a previous session and continue the dialogue  |
| `/verbose [true\|false]`  | Toggle display of bash commands in agent mode      |

```bash
# List recent sessions
/sessions

# Resume a previous session
/resume 20260511_143022
```

## Skills

Skills are reusable prompt templates stored as Markdown files. Invoke them with a slash command in chat or from the terminal.

```markdown
skills/
  code-review/code-review.md
  code-explain/code-explain.md
  my-skill/my-skill.md        ← your custom skill
```

Each skill file starts with a frontmatter block:

```markdown
---
description : One-line description shown in /skill list
---

Your prompt text here. Use $ARGUMENTS for user-supplied arguments.
```

**Built-in skills:**

| Command         | Description                                      |
|-----------------|--------------------------------------------------|
| `/code-review`  | Review code for style, bugs, and improvements   |
| `/code-explain` | Explain what a piece of code does               |
| `/skill-creator`| Interactive wizard that creates new skill files |

```bash
# List all available skills
/skill

# Use a skill with arguments
/code-review src/main.py

# From terminal (single-turn)
ai /code-explain "$(cat utils.py)"
```

## Telegram

Connect the bot to your Telegram account to send prompts and receive answers without opening the terminal.

**Setup:**

1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token
2. Add to `ai.ini`:

```ini
[telegram]
token       = "123456:ABC-your-token"
allowed_ids = "@username1, @username2"  # leave empty to allow all
autostart   = false                     # true = start bot on chat launch
```

**Usage:**

```bash
# Start bot in standalone mode (Ctrl+C to stop)
ai -t

# Or start alongside interactive chat
ai
/telegram
```

Once running, send any message to your bot in Telegram. Shell agent and all skills are available — e.g. `/code-review` or any bash-capable prompt.

## Proxy support

If specific LLM provider or Telegram messenger not available in your region,
Socks5 proxy supported via eviroment variable, 'ALL_PROXY=socks5://<IP>:<PORT> ai' 
 


## Supported LLM Providers

| Provider    | Default model from ai.ini |
|-------------|----------------------|
| OpenRouter  | `openrouter/free`    |
| DeepSeek    | `deepseek-v4-flash`  |
| OpenAI      | `gpt-5.4-mini`       |
| Anthropic   | `claude-sonnet-4-6`  |
| Google      | `gemini-2.5-flash`   |
| XAI         | `grok-4.1-fast`      |

OpenRouter provides access to many models through a single API key.
Free models have the `free` suffix. Full list: `ai -p openrouter -lm`

## API Keys

Access to provider models requires API keys.
They can be set via environment variables or in `ai.ini` under the `[api_keys]` section:

| Provider         | Environment variable | API Key URL |
|------------------|----------------------|-------------|
| DeepSeek         | `DEEPSEEK_API_KEY`   | https://platform.deepseek.com/api_keys |
| OpenRouter       | `OPENROUTER_API_KEY` | https://openrouter.ai/settings/keys |
| Anthropic Claude | `ANTHROPIC_API_KEY`  | https://console.anthropic.com/settings/keys |
| OpenAI ChatGPT   | `OPENAI_API_KEY`     | https://platform.openai.com/api-keys |
| Google Gemini    | `GEMINI_API_KEY`     | https://aistudio.google.com/app/apikey |
| XAI Grok         | `XAI_API_KEY`        | https://console.x.ai/team/default/api-keys |

[Changelog](CHANGELOG.md)

---