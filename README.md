# AI.SHELL 

CLI-утилита для работы с различными LLM API из терминала: Google Gemini, OpenAI ChatGpt, XAI Grok, DeepSeek, Anthropic Claude.

## Установка

рекомендуется через менеджер UV 
если он не установлен

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
установка AI.SHELL

```bash
uv tool install git+https://github.com/voepiter/ai.shell.git

```

## Конфигурация

файл `ai.ini` создается при первом запуске мастером, настройки по умолчанию из `ai.ini.example`:

### API ключи

Задаются через переменные окружения env или из ai.ini в секции [api_keys]:

| Провайдер   | Переменная окружения  |
|-------------|-----------------------|
| Gemini      | `GEMINI_API_KEY`      |
| OpenAI      | `OPENAI_API_KEY`      |
| XAI         | `XAI_API_KEY`        |
| DeepSeek    | `DEEPSEEK_API_KEY`    |
| Anthropic   | `ANTHROPIC_API_KEY`   |
| OpenRouter  | `OPENROUTER_API_KEY`  |

## Использование

```bash
# Интерактивный режим с bash агентом
ai

# Одиночный запрос
ai "ваш запрос"

# Выбор провайдера и модели
ai -p openai -m gpt-5.4 "ваш запрос"

# Системная инструкция
ai -i "You are a Python expert" "напиши функцию для сортировки"

# Ассистент из конфига
ai -a admin "напиши docker-compose для nginx"

# Список провайдеров
ai -lp
# Cписок моделей
ai -p deepseek -lm
```

## Опции командной строки

| Опция                   | Описание                                           |
|-------------------------|----------------------------------------------------|
| `prompt`                | Текст запроса к AI                                 |
| `-p` / `--provider`     | Провайдер: `gemini`, `openai`, `xai`, `deepseek`, `anthropic` |
| `-m` / `--model`        | Имя модели                                         |
| `-i` / `--instruction`  | Системная инструкция                               |
| `-a` / `--assistant`    | Имя ассистента из `ai.ini`                        |
| `-l` / `--list-models`  | Показать список доступных моделей и выйти          |

## Поддерживаемые провайдеры

| Провайдер   | Модель по умолчанию                        |
|-------------|---------------------------------------------|
| Gemini      | `gemini-2.5-flash`                          |
| OpenAI      | `gpt-4.1-mini`                              |
| XAI         | `grok-3-mini`                               |
| DeepSeek    | `deepseek-v4-flash`                             |
| Anthropic   | `claude-sonnet-4-6`                         |
| OpenRouter  | `openrouter/free`    |

OpenRouter даёт доступ к множеству моделей через один API ключ.
Бесплатные модели имеют суффикс `:free`. Полный список: `ai -p openrouter -lm`

## Приоритет настроек

1. Аргументы командной строки (`-p`, `-m`, `-i`, `-a`)
2. Конфиг `ai.ini` (`[providers].default`, `[assistant].default`)
3. Значения по умолчанию

## Структура проекта
