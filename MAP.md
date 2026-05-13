# Project Map

Multi-model LLM CLI client + bash agent.

---

## Entry Point

ai.py  67  Entry point — parses args, routes to setup / single-turn / interactive chat.
	_early_lang  Read language from -l argv or ai.ini [ui] language before parser is built.
	main  Parse args, set locale early, dispatch to setup / single_turn / chat.

---

## modules/

agent.py  126  Shell agent loop — iterative bash command execution and LLM interaction.
	build_system_instruction(base, shell_mode)  Append shell hint to system instruction when shell mode is active.
	agentic_loop(history, text, api_client, config, logger, request_counter, shell_mode, total_in, total_out, total_elapsed, verbose)  Run bash commands from LLM response, feed output back, repeat until no commands remain.

api.py  72  Factory for creating API provider clients.
	APIFactory.create_client(provider, api_key, model, timeout, config_loader)  Instantiate the right provider client; resolves api_key from env or ai.ini.

chat.py  111  Interactive REPL loop.
	run(state)  Run interactive chat loop — handles input, slash commands, and agent dispatch.

colors.py  28

commands.py  192  Slash-command dispatcher for interactive chat (/help, /model, /provider, /shell, /verbose, /sessions, /resume …).
	handle(raw, history, state)  Route slash command to handler; return 'quit', 'reset', or None.
	_cmd_sessions(log_dir)  Print table of 10 most recent sessions from JSONL logs.
	_cmd_resume(session_id, history, log_dir)  Load session history into active conversation and display transcript.

config.py  94  Configuration — TOML file loader and typed runtime config.
	ConfigLoader  Reads ai.ini (TOML); resolves path from cwd, script dir, or ~/.config/ai-shell/.
	ConfigLoader.get(*keys)  Look up a nested key path in config; return default if any key is missing.

counter.py  6  Per-session request counter, starts at 1.

locale.py  65  Language detection and translated string lookup.
	set_lang(lang)  Load strings for lang code (falls back to en); return resolved code.
	t(*keys, **fmt)  Look up translated string by section + key; format with kwargs.

logger.py  51  Per-session JSONL logger.
	Logger  Writes one JSONL file per session to log_dir/YYYYMMDD_HHMMSS.jsonl.
	Logger.log_user(content)  Append user message to session log.
	Logger.log_tool(content)  Append agent tool-call result to session log.
	Logger.log_assistant(content, model, tokens_in, tokens_out, elapsed)  Append assistant response with model and token metadata.

logo.py  59  ASCII logo display with lolcat-style rainbow gradient.
	print_logo(path, delay, logo_gradient)  Print ASCII logo with animated rainbow gradient; skip silently if file missing.

parser.py  37  CLI argument parser.
	build  Build and return the argparse parser with localised help strings.

setup.py  218  First-run setup wizard — creates ai.ini from ai.ini.default.

shell.py  70  Shell command executor for agent mode.
	CommandResult.to_context  Format result as context string for LLM (stdout, stderr, exit code).
	extract_commands(text)  Extract bash commands from <bash>…</bash> tags or markdown code blocks.
	is_dangerous(command, patterns)  Return True if command matches any dangerous pattern from config.
	run_command(command, timeout)  Run shell command, capture stdout/stderr; return CommandResult.

single_turn.py  68  Single-turn (non-interactive) request handler.
	run(state, prompt)  Send one prompt, print response; runs agent loop if shell commands are detected.

spinner.py  56  Animated status spinner shown while waiting for LLM response.

state.py  48  Shared runtime state passed across all modules.
	AppState.from_args(args)  Build AppState from parsed CLI args and ai.ini config.

symbols.py  19  Terminal symbols — unicode or ASCII depending on ai.ini [ui] unicode setting.

text.py  71  Terminal text rendering — ANSI colors and markdown highlighting.

ui.py  137  Terminal rendering — banners, stats, model/provider lists.
	print_banner(provider, model, shell_mode, verbose)  Print interactive mode header with provider, model, shell/verbose status.
	print_chat_help  Print available slash commands.
	print_stats(token_in, token_out, elapsed, request_num)  Print token usage and elapsed time for one request.
	print_providers(config_loader)  Print all providers with default model and env var name.
	print_models(provider, api_client, config_loader)  Fetch and print available models for provider; mark default.

version.py  19  Version resolution — installed package metadata or pyproject.toml fallback.
	get_version  Return version from installed package metadata or pyproject.toml fallback.

---

## providers/

anthropic.py  60  Anthropic Claude API client (api.anthropic.com/v1/messages).

base.py  99  Abstract base client and APIError — shared by all provider implementations.

deepseek.py  42  DeepSeek API client (api.deepseek.com/v1/chat/completions).

google.py  55  Google Gemini API client (generativelanguage.googleapis.com).

openai.py  58  OpenAI API client (api.openai.com/v1/chat/completions).

openrouter.py  55  OpenRouter API client — unified gateway to multiple LLM providers (openrouter.ai/api/v1).

xai.py  42  xAI Grok API client (api.x.ai/v1/chat/completions).

---

## Config & data files

locales/en.toml  English UI strings — [unicode][keys][settings][ui][common][commands][parser][agent]
locales/ru.toml  Russian UI strings — same sections as en.toml
ai.ini.default   Template / reference config
pyproject.toml   Package build config (name=ai.shell, entry point: ai=ai:main)
