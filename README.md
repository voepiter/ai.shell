# AI CLI Tool

CLI-утилита для работы с различными LLM API: Google Gemini, OpenAI, XAI (Grok), DeepSeek, Anthropic Claude.

## Установка

```bash
pip install -r requirements.txt
```

## Конфигурация

Создайте файл `ai.ini` (см. `ai.ini.example`):

```bash
cp ai.ini.example ai.ini
```

### API ключи

Задаются через переменные окружения:

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
# Простой запрос (провайдер из ai.ini)
ai "ваш запрос"

# Выбор провайдера и модели
ai -p openai -m gpt-4.1 "ваш запрос"

# Системная инструкция
ai -i "You are a Python expert" "напиши функцию для сортировки"

# Ассистент из конфига
ai -a devops "напиши docker-compose для nginx"

# Список моделей провайдера
ai -l
ai -p anthropic -l
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
| DeepSeek    | `deepseek-chat`                             |
| Anthropic   | `claude-sonnet-4-6`                         |
| OpenRouter  | `meta-llama/llama-3.3-70b-instruct:free`    |

OpenRouter даёт доступ к сотням моделей (GPT, Claude, Llama, Gemini и др.) через один API ключ.
Бесплатные модели имеют суффикс `:free`. Полный список: `ai -p openrouter -l`

## Приоритет настроек

1. Аргументы командной строки (`-p`, `-m`, `-i`, `-a`)
2. Конфиг `ai.ini` (`[providers].default`, `[assistant].default`)
3. Значения по умолчанию

## Добавление нового провайдера

1. Создайте `providers/new_provider.py`, унаследуйтесь от `BaseAPIClient`
2. Реализуйте `_make_request()`, `extract_response()`, `extract_usage()`, `list_models()`
3. Добавьте провайдер в `api.py` в словари `PROVIDERS`, `API_KEY_ENV_VARS`

## Структура проекта

```
ai/
├── ai.py                 # Точка входа
├── cli.py                # CLI и основная логика
├── config.py             # Конфигурация
├── config_loader.py      # Загрузчик TOML конфига
├── api.py                # Фабрика для создания клиентов
├── providers/            # Провайдеры API
│   ├── base.py           # Базовый класс
│   ├── gemini.py
│   ├── openai.py
│   ├── xai.py
│   ├── deepseek.py
│   └── anthropic.py
├── logger.py             # Логирование
├── spinner.py            # Индикатор загрузки
├── RequestCounter.py     # Счётчик запросов
├── ColoredText.py        # Цветной вывод
├── requirements.txt      # Зависимости
├── ai.ini               # Конфиг (создайте из примера)
└── ai.ini.example       # Пример конфига
```
