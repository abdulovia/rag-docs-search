# RAG Document Search

Production-grade RAG система для поиска информации в документах на основе генерации с дополненной выборкой (Retrieval-Augmented Generation).

## Prerequisites

### Обязательные зависимости

| Зависимость | Минимальная версия | Проверка |
|-------------|-------------------|----------|
| **Docker** | 20.10+ | `docker --version` |
| **Docker Compose** | 2.0+ | `docker-compose --version` |
| **GNU Make** | любая | `make --version` |

> **Примечание:** Python и pip не нужны для Docker-вариата. Все зависимости устанавливаются внутри контейнеров.

### Проверка установки

```bash
# Проверить Docker
docker --version
# Docker version 24.0.7, build afdd53b

# Проверить Docker Compose
docker-compose --version
# docker-compose version 1.29.2

# Проверить Make
make --version
# GNU Make 4.3
```

## Быстрый старт (Docker)

### Шаг 1: Клонировать репозиторий

```bash
git clone <repository-url>
cd rag-docs-search
```

### Шаг 2: Настроить окружение

```bash
# Скопировать пример конфигурации
cp .env.example .env

# Проверить что файл .env создан
cat .env
```

### Шаг 3: Собрать образы

```bash
# Собрать все образы (первый раз ~5 минут)
docker-compose build
```

> **Оптимизация сборки:** Dockerfile использует multi-stage build и отдельную установку heavy-пакетов для кэширования. При первой сборке:
> 1. Скачивается базовый образ Python (~150MB)
> 2. Устанавливаются системные зависимости (~50MB)
> 3. Устанавливаются Python пакеты (~400MB)
> 
> Повторная сборка использует кэш Docker и занимает ~10 секунд.

### Шаг 4: Запустить систему

```bash
# Запустить все сервисы
docker-compose up -d

# Проверить статус (должны быть 3 контейнера)
docker ps | grep rag
```

Ожидаемый вывод:
```
rag-ollama   Up   0.0.0.0:11434->11434/tcp
rag-api      Up   0.0.0.0:8000->8000/tcp
rag-ui       Up   0.0.0.0:8501->8501/tcp
```

### Шаг 5: Скачать модель Ollama

```bash
# Скачать модель для генерации (~2GB, занимает 5-10 минут)
docker exec rag-ollama ollama pull llama3.2:3b-instruct-fp16

# Проверить что модель скачалась
docker exec rag-ollama ollama list
```

### Шаг 6: Проверить систему

```bash
# Проверить API
curl http://localhost:8000/api/v1/health

# Проверить UI
curl http://localhost:8501/_stcore/health

# Открыть в браузере
# UI: http://localhost:8501
# API Docs: http://localhost:8000/docs
```

## Управление через Makefile

```bash
# Запустить все сервисы
make start

# Остановить все сервисы
make stop

# Перезапустить
make restart

# Показать статус
make status

# Показать логи
make logs

# Пересобрать только API (быстро)
make rebuild-api

# Пересобрать только UI (быстро)
make rebuild-ui

# Полная пересборка (очистка кэша)
make redeploy
```

## Индексация документов

### Поддерживаемые форматы

- **PDF** (.pdf) — через PyMuPDF
- **Markdown** (.md, .markdown) — с сохранением структуры

### Способы индексации

**1. Через UI:**
1. Откройте http://localhost:8501
2. В sidebar нажмите "Upload PDF or Markdown"
3. Выберите файл
4. Нажмите "Загрузить и проиндексировать"

**2. Через API:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf"
```

**3. Через CLI:**
```bash
# Поместите документы в data/documents/
make index-docs
```

## Конфигурация

Все настройки через `.env` файл:

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `API_PORT` | Порт API | 8000 |
| `UI_PORT` | Порт UI | 8501 |
| `OLLAMA_PORT` | Порт Ollama | 11434 |
| `LLM_MODEL_NAME` | Модель Ollama | llama3.2:3b-instruct-fp16 |
| `EMBEDDING_MODEL_NAME` | Embedding модель | intfloat/multilingual-e5-large |
| `RETRIEVAL_TOP_K` | Количество результатов | 5 |
| `RETRIEVAL_MIN_SCORE` | Минимальный score | 0.0 |
| `RETRIEVAL_SIMILARITY_THRESHOLD` | Порог similarity | 0.0 |
| `ENABLE_WEB_SEARCH` | Веб-поиск | true |
| `ENABLE_SELF_CORRECTION` | Self-RAG | false |
| `OLLAMA_KEEP_ALIVE` | Время жизни модели в VRAM | 1m |

## API Endpoints

### Chat

```bash
# Задать вопрос
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Что такое RAG?", "top_k": 5, "enable_web_search": false}'

# С веб-поиском
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Какой сейчас год?", "enable_web_search": true}'
```

### Documents

```bash
# Загрузить документ
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf"

# Список документов
curl "http://localhost:8000/api/v1/documents"

# Удалить документ
curl -X DELETE "http://localhost:8000/api/v1/documents/filename.pdf"

# Переиндексировать все
curl -X POST "http://localhost:8000/api/v1/documents/reindex"
```

### Health

```bash
curl "http://localhost:8000/api/v1/health"
```

## Docker оптимизации

### Multi-stage build

Dockerfile использует multi-stage build для уменьшения размера образа:

```dockerfile
# Stage 1: Установка зависимостей
FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime (только нужное)
FROM python:3.12-slim AS runtime
COPY --from=builder /usr/local/lib/python3.12/site-packages ...
```

### Кэширование

- **Системные пакеты** — кэшируются Docker
- **Python пакеты** — кэшируются при неизменном `requirements.txt`
- **Код** — пересобирается только при изменении

### Отдельная установка heavy-пакетов

Для ускорения сборки heavy-пакеты устанавливаются отдельно:

```dockerfile
# Установка torch отдельно (кэшируется)
RUN pip install --no-cache-dir torch

# Остальные пакеты
RUN pip install --no-cache-dir -r requirements.txt
```

### Размеры образов

| Образ | Размер |
|-------|--------|
| rag-docs-search-api | ~600MB |
| rag-docs-search-ui | ~750MB |
| ollama/ollama | ~9GB (с моделями) |

## Структура проекта

```
rag-docs-search/
├── src/
│   ├── domain/                  # Доменная логика
│   │   ├── entities/            # Document, Query, Response
│   │   ├── value_objects/       # ChunkConfig, RetrievalConfig
│   │   ├── ports/               # Protocol интерфейсы
│   │   └── exceptions.py
│   ├── application/             # Use cases
│   │   ├── use_cases/           # AnswerQuestion, IndexDocuments
│   │   ├── services/            # PromptRegistry
│   │   └── dto/                 # Request/Response DTO
│   ├── infrastructure/          # Реализации
│   │   ├── config/              # Pydantic Settings
│   │   ├── parsers/             # PDF, Markdown парсеры
│   │   ├── chunkers/            # Parent-Child чанкинг
│   │   ├── embeddings/          # HuggingFace embeddings
│   │   ├── vector_stores/       # FAISS реализация
│   │   ├── retrievers/          # Vector retriever
│   │   ├── rerankers/           # Cross-encoder reranker
│   │   ├── llm/                 # Ollama клиент
│   │   ├── evaluation/          # RAG evaluator
│   │   ├── prompts/             # Jinja2 шаблоны
│   │   └── monitoring/          # Loguru логирование
│   └── interfaces/
│       ├── api/                 # FastAPI
│       └── ui/                  # Streamlit
├── tests/
│   ├── unit/                    # Unit тесты
│   ├── integration/             # Integration тесты
│   └── evaluation/              # Quality тесты
├── docker/
│   ├── Dockerfile.api           # API образ
│   └── Dockerfile.ui            # UI образ
├── data/documents/              # Документы для индексации
├── logs/                        # Логи
├── main.py                      # Entry point
├── requirements.txt             # Зависимости (полные)
├── requirements-docker.txt      # Зависимости (для Docker)
├── docker-compose.yaml          # Docker Compose
├── Makefile                     # Автоматизация
├── .env.example                 # Пример конфигурации
└── AGENTS.md                    # Инструкции для AI
```

## Логи

### Просмотр логов

```bash
# Все логи
make logs

# Только API
docker logs rag-api --tail 50

# Только UI
docker logs rag-ui --tail 50

# Только Ollama
docker logs rag-ollama --tail 50

# В реальном времени
docker logs -f rag-api
```

### Файлы логов

Логи пишутся в папку `logs/`:

```
logs/
├── app.log        # Основной лог
├── debug.log      # DEBUG логи
├── error.log      # Ошибки
└── rag.log        # RAG pipeline логи
```

### Уровни логирования

| Уровень | Описание |
|---------|----------|
| DEBUG | Подробная отладка |
| INFO | Основные события |
| WARNING | Предупреждения |
| ERROR | Ошибки |

Настройка в `.env`:
```
MONITORING_LOG_LEVEL=DEBUG
```

## Архитектура

Проект построен по принципам **Clean Architecture**:

```
Interfaces → Application → Domain ← Infrastructure
```

### Слои

1. **Domain** — чистая бизнес-логика, не зависит ни от чего
2. **Application** — use cases, зависит только от Domain
3. **Infrastructure** — реализации портов (FAISS, Ollama, HuggingFace)
4. **Interfaces** — API и UI, зависит от Application

### RAG Pipeline

```
1. Retrieval — поиск документов (score >= 0.2)
2. Generation — генерация ответа из контекста
3. Answered Check — проверка ответил ли LLM
   - Да → [Из документов]
   - Нет → direct LLM → [Сгенерировано]
4. Web Search — если включен и документы не найдены
   → [Из интернета]
```

## Остановка

```bash
# Остановить все сервисы (сохранить данные)
docker-compose down

# Остановить и удалить данные
docker-compose down -v

# Остановить через Makefile
make stop
```

> **Важно:** Никогда не удаляйте образ `ollama/ollama` — он весит ~9GB!

## Лицензия

MIT
