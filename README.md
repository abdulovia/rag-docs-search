# RAG Document Search

Production-grade RAG система для поиска информации в документах на основе генерации с дополненной выборкой (Retrieval-Augmented Generation).

## Prerequisites

Перед началом работы убедитесь, что у вас установлены:

### Обязательные зависимости

- **Python 3.10+**
- **Docker** (для запуска Ollama)
- **pip** или **pip3**

### Проверка установки

```bash
# Проверить Python
python3 --version

# Проверить Docker
docker --version

# Проверить pip
pip3 --version
```

## Быстрый старт

### Вариант 1: Docker (рекомендуется)

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd rag-docs-search

# 2. Скопировать конфигурацию
cp .env.example .env

# 3. Запустить все сервисы
docker-compose up -d

# 4. Подождать пока Ollama запустится и скачать модель
sleep 30
docker exec rag-ollama ollama pull llama3.2:3b-instruct-fp16

# 5. Открыть в браузере
# UI: http://localhost:8501
# API: http://localhost:8000/docs
```

Остановка:
```bash
docker-compose down
```

### Вариант 2: Локальная установка

### 1. Клонировать репозиторий

```bash
git clone <repository-url>
cd rag-docs-search
```

### 2. Установить зависимости Python

```bash
# Через Makefile (рекомендуется)
make install

# Или вручную
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Настройка Ollama

```bash
# Запустить Ollama в Docker
make ollama-start

# Дождаться запуска (10-15 секунд)
sleep 15

# Скачать модель для генерации
make ollama-pull MODEL=llama3.2:3b-instruct-fp16

# Проверить что Ollama работает
curl http://localhost:11434/api/tags
```

### 4. Конфигурация

```bash
# Скопировать пример конфигурации
cp .env.example .env

# При необходимости отредактировать настройки
# nano .env
```

### 5. Запуск API

```bash
# Запустить API в фоне
nohup python3 main.py > logs/api.log 2>&1 &

# Проверить статус
curl http://localhost:8000/api/v1/health
```

### 6. Запуск UI (в отдельном терминале)

```bash
streamlit run src/interfaces/ui/streamlit_app.py --server.port 8501
```

UI будет доступен на http://localhost:8501

## Установка зависимостей

### Python пакеты

```bash
pip install -r requirements.txt
```

### Основные зависимости

| Пакет | Версия | Назначение |
|-------|--------|------------|
| pydantic | >=2.0.0 | Валидация данных |
| pydantic-settings | >=2.0.0 | Конфигурация |
| fastapi | >=0.109.0 | REST API |
| uvicorn | >=0.27.0 | ASGI сервер |
| streamlit | >=1.30.0 | UI |
| pymupdf | >=1.23.0 | PDF парсинг |
| sentence-transformers | >=3.0.0 | Embeddings |
| faiss-cpu | >=1.7.0 | Векторная БД |
| loguru | >=0.7.0 | Логирование |

### ML зависимости (устанавливаются автоматически)

- **torch** — PyTorch для ML моделей
- **transformers** — HuggingFace transformers
- **sentence-transformers** — Embedding модели

## API Endpoints

### Chat

```bash
# Задать вопрос
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Что такое RAG?", "top_k": 5}'
```

### Documents

```bash
# Загрузить документ
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf"

# Список документов
curl "http://localhost:8000/api/v1/documents"
```

### Health

```bash
# Проверка здоровья
curl "http://localhost:8000/api/v1/health"
```

## Конфигурация

Все настройки через `.env` файл:

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `ENVIRONMENT` | Окружение | development |
| `DEBUG` | Режим отладки | true |
| `LLM_MODEL_NAME` | Модель Ollama | llama3.2:3b-instruct-fp16 |
| `LLM_OLLAMA_URL` | URL Ollama | http://localhost:11434 |
| `EMBEDDING_MODEL_NAME` | Embedding модель | intfloat/multilingual-e5-large |
| `EMBEDDING_DEVICE` | Устройство | cpu |
| `RETRIEVAL_TOP_K` | Количество результатов | 5 |
| `RETRIEVAL_ENABLE_RERANKING` | Включить reranking | true |
| `VECTOR_PROVIDER` | Векторная БД | faiss |
| `ENABLE_SELF_CORRECTION` | Self-RAG проверка | true |
| `MONITORING_LOG_LEVEL` | Уровень логирования | INFO |

## Команды Makefile

```bash
# Установка
make install              # Установить зависимости

# Ollama
make ollama-start         # Запустить Ollama (Docker)
make ollama-stop          # Остановить Ollama
make ollama-restart       # Перезапустить Ollama
make ollama-pull MODEL=   # Скачать модель

# Запуск
make run-api              # Запустить API сервер
make run-ui               # Запустить Streamlit UI

# Тестирование
make test                 # Запустить все тесты
make test-unit            # Только unit тесты
make lint                 # Линтинг кода

# Индексация
make index-docs           # Индексировать документы из data/documents/

# Очистка
make clean                # Удалить venv, кэш, логи
```

## Индексация документов

### Поддерживаемые форматы

- **PDF** (.pdf) — через PyMuPDF
- **Markdown** (.md, .markdown) — с сохранением структуры

### Способы индексации

**1. Через API:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf"
```

**2. Через CLI:**
```bash
# Поместите документы в data/documents/
make index-docs
```

**3. Через UI:**
Загрузите документ через веб-интерфейс на http://localhost:8501

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
├── data/documents/              # Документы для индексации
├── configs/                     # Конфиги
├── docs/                        # Документация
├── main.py                      # Entry point
├── requirements.txt             # Зависимости
├── Makefile                     # Автоматизация
├── .env.example                 # Пример конфигурации
└── AGENTS.md                    # Инструкции для AI
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

### Protocol-based DI

Все интерфейсы определяются через `typing.Protocol`:

```python
from typing import Protocol

class Retriever(Protocol):
    async def retrieve(self, query: Query, top_k: int = 5): ...
```

## Расширяемость

### Добавление нового LLM

1. Создайте файл в `src/infrastructure/llm/`
2. Реализуйте `LLMClient` Protocol
3. Обновите DI в `src/interfaces/api/dependencies.py`

### Добавление новой векторной БД

1. Создайте файл в `src/infrastructure/vector_stores/`
2. Реализуйте `VectorStore` Protocol
3. Обновите DI factory

## Типичные проблемы

### Ollama не запускается

```bash
# Проверить логи Docker
docker logs ollama-docker

# Перезапустить
make ollama-restart
```

### Модель не скачивается

```bash
# Проверить доступное место на диске
df -h

# Попробовать скачать вручную
docker exec -it ollama-docker ollama pull llama3.2:3b-instruct-fp16
```

### Import errors

```bash
# Убедиться что все зависимости установлены
pip install -r requirements.txt

# Обновить pip
pip install --upgrade pip
```

## Лицензия

MIT
