[English](README.md) | [Русский](README.ru.md)

# AI.SHELL


утилита для работы с различными LLM API из терминала: Openrouter, DeepSeek, OpenAI ChatGpt, Anthropic Claude, Google Gemini, XAI Grok.

## Установка

рекомендуется через менеджер пакетов UV 

если он не установлен

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
установка AI.SHELL

```bash
uv tool install git+https://github.com/voepiter/ai.shell.git

```

## Конфигурация

файл `ai.ini` создается при первом запуске мастером, настройки по умолчанию из `ai.ini.default`:

### API ключи

Для доступа к моделям LLM вам нужны API ключи
Они задаются через переменные окружения или из ai.ini в секции [api_keys]:

| Провайдер        | Переменная окружения |
|------------------|----------------------|
| DeepSeek         | `DEEPSEEK_API_KEY`   |
| Anthropic Claude | `ANTHROPIC_API_KEY`  |
| OpenAI ChatGPT   | `OPENAI_API_KEY`     |
| XAI Grok         | `XAI_API_KEY`        |
| Google Gemini    | `GOOGLE_API_KEY`     |
| OpenRouter       | `OPENROUTER_API_KEY` |

## Использование

```bash
# Интерактивный режим с bash агентом
ai

# Одиночный запрос
ai "ваш запрос"

# Выбор провайдера и модели
ai -p openai -m gpt-5.3-mini "ваш запрос"

# Системная инструкция
ai -i "You are a Python expert" "напиши функцию для сортировки"

# Список провайдеров
ai -lp
# Cписок моделей
ai -p openrouter -lm
```

## Опции командной строки

| Опция                     | Описание                     |
|---------------------------|------------------------------|
| `"prompt"`                | Текст запроса к AI           |
| `-h` / `--help`           | Вывод справки по опциям      |
| `-l` / `--language`       | Выбор языка                  |
| `-i` / `--instruction`    | Системная инструкция         |
| `-p` / `--provider`       | Провайдер                    |
| `-m` / `--model`          | Имя модели                   |
| `-lp`/ `--list-providers` | Cписок доступных провайдеров |
| `-lm`/ `--list-models`    | Cписок доступных моделей     |


## Поддерживаемые провайдеры

| Провайдер   | Модель по умолчанию  |
|-------------|----------------------|
| OpenRouter  | `openrouter/free`    |
| DeepSeek    | `deepseek-v4-flash`  |
| OpenAI      | `gpt-5.4-mini`       |
| Anthropic   | `claude-sonnet-4-6`  |
| Google      | `gemini-2.5-flash`   |
| XAI         | `grok-4.1-fast`      |

OpenRouter даёт доступ к множеству моделей через один API ключ.
Бесплатные модели имеют суффикс `free`. Полный список: `ai -p openrouter -lm`


