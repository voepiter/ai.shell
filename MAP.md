# Project Map

Multi-model LLM CLI client + bash agent.

---

## Entry Point

ai.py  78  Entry point — parses args, routes to setup / single-turn / interactive chat.
	_early_lang  Read language from -l argv or ai.ini [ui] language before parser is built.
	main  Parse args, set locale early, dispatch to setup / single_turn / chat.

---

## modules/

agent.py  126  Shell agent loop — iterative bash command execution and LLM interaction.
	build_system_instruction(base, shell_mode)  Append shell hint to system instruction when shell mode is active.
	agentic_loop(history, text, api_client, config, logger, request_counter, shell_mode, total_in, total_out, total_elapsed, verbose)  Run bash commands from LLM response, feed output back, repeat until no commands remain.

api.py  72  Factory for creating API provider clients.
	APIFactory.create_client(provider, api_key, model, timeout, config_loader)  Instantiate the right provider client; resolves api_key from env or ai.ini.

chat.py  116  Interactive REPL loop.
	run(state)  Run interactive chat loop — handles input, slash commands, and agent dispatch.

colors.py  29

commands.py  213  Slash-command dispatcher for interactive chat (/help, /model, /provider, /shell, /verbose, /sessions, /resume …).
	handle(raw, history, state)  Route slash command to handler; return 'quit', 'reset', or None.
	_cmd_skills(config_loader)  Print table of available skills with descriptions.
	_cmd_sessions(log_dir)  Print table of 10 most recent sessions from JSONL logs.
	_cmd_resume(session_id, history, log_dir)  Load session history into active conversation and display transcript.

config.py  159  Configuration — TOML file loader, typed runtime config, and config migration.
	ConfigLoader  Reads ai.ini (TOML); resolves path from cwd, script dir, or ~/.config/ai-shell/.
	ConfigLoader.get(*keys)  Look up a nested key path in config; return default if any key is missing.
	_raw_lines(path)  Parse a config file and return {section: {key: raw_line}} for migration.
	_insert_into_section(content, section, lines)  Append lines at the end of a named section in config file text.
	migrate_config(config_loader)  Add keys from ai.ini.default that are missing from the user's ai.ini.

counter.py  6  Per-session request counter, starts at 1.

locale.py  65  Language detection and translated string lookup.
	set_lang(lang)  Load strings for lang code (falls back to en); return resolved code.
	t(*keys, **fmt)  Look up translated string by section + key; format with kwargs.

logger.py  51  Per-session JSONL logger.
	Logger  Writes one JSONL file per session to log_dir/YYYYMMDD_HHMMSS.jsonl.
	Logger.log_user(content)  Append user message to session log.
	Logger.log_tool(content)  Append agent tool-call result to session log.
	Logger.log_assistant(content, model, tokens_in, tokens_out, elapsed)  Append assistant response with model and token metadata.

logo.py  61  ASCII logo display with lolcat-style rainbow gradient.
	print_logo(path, delay, logo_gradient)  Print ASCII logo with animated rainbow gradient; skip silently if file missing.

parser.py  32  CLI argument parser.
	build  Build and return the argparse parser with localised help strings.

setup.py  200  First-run setup wizard — creates ai.ini from ai.ini.default.

shell.py  70  Shell command executor for agent mode.
	CommandResult.to_context  Format result as context string for LLM (stdout, stderr, exit code).
	extract_commands(text)  Extract bash commands from <bash>…</bash> tags or markdown code blocks.
	is_dangerous(command, patterns)  Return True if command matches any dangerous pattern from config.
	run_command(command, timeout)  Run shell command, capture stdout/stderr; return CommandResult.

single_turn.py  68  Single-turn (non-interactive) request handler.
	run(state, prompt)  Send one prompt, print response; runs agent loop if shell commands are detected.

skills.py  67  Skill loader — discovers and loads .md skill files from skill directories.
	_dirs(config_loader)  Return skill search paths: user config dir first, then bundled package skills.
	_find(name, config_loader)  Return path to skills/name/name.md or None if not found.
	_parse(path, args)  Strip YAML frontmatter, substitute $ARGUMENTS; return (content, description).
	load(raw_input, config_loader)  Parse /name [args] input; return skill content with $ARGUMENTS substituted, or None.
	list_skills(config_loader)  Return sorted (name, description) pairs for all available skills.

spinner.py  56  Animated status spinner shown while waiting for LLM response.

state.py  48  Shared runtime state passed across all modules.
	AppState.from_args(args)  Build AppState from parsed CLI args and ai.ini config.

symbols.py  19  Terminal symbols — unicode or ASCII depending on ai.ini [ui] unicode setting.

text.py  71  Terminal text rendering — ANSI colors and markdown highlighting.

ui.py  138  Terminal rendering — banners, stats, model/provider lists.
	print_banner(provider, model, shell_mode, verbose)  Print interactive mode header with provider, model, shell/verbose status.
	print_chat_help  Print available slash commands.
	print_stats(token_in, token_out, elapsed, request_num)  Print token usage and elapsed time for one request.
	print_providers(config_loader)  Print all providers with default model and env var name.
	print_models(provider, api_client, config_loader)  Fetch and print available models for provider; mark default.

updates.py  105  Auto-update — once per day checks GitHub for a newer release and runs uv tool update.
	_check_path(config_loader)  Return path to the last-check date file, stored next to ai.ini.
	_checked_today(path)  Return True if the check file contains today's date.
	_mark_checked(path)  Write today's date to the check file.
	_newer(latest, current)  Return True if latest version tuple is greater than current.
	_fetch_latest(timeout)  Fetch latest release tag from GitHub; return version string or None.
	_changelog_section(version, timeout)  Fetch CHANGELOG.md from GitHub and return the section for version.
	check_and_update(config_loader)  Check once per day for a newer release; update and show changelog if found.

version.py  46  Version resolution — installed package metadata or pyproject.toml fallback.
	get_version  Return version as major.minor.{git_commit_count}, falling back to package metadata.

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
