# AGENTS.md - Инструкции для AI ассистентов

## Контекст проекта

Это RAG-система для поиска информации в документах на основе генерации с дополненной выборкой (Retrieval-Augmented Generation). Проект является частью дипломной работы (ВКР).

## Архитектура

Система построена по принципам **Clean Architecture** с 4 слоями:

```
src/
├── domain/          # Слой 1: Domain (ядро бизнес-логики)
│   ├── entities/    # Бизнес-объекты (Document, Query, Response)
│   ├── value_objects/ # Неизменяемые значения (Embedding, Score)
│   └── ports/       # Абстракции (интерфейсы через Protocol)
├── application/     # Слой 2: Application (use cases)
│   ├── use_cases/   # Основные операции
│   ├── services/    # Сервисы приложения
│   └── dto/         # Data Transfer Objects
├── infrastructure/  # Слой 3: Infrastructure (реализации)
│   ├── config/      # Конфигурация (Pydantic Settings)
│   ├── parsers/     # Документ-парсеры (PDF, Markdown)
│   ├── chunkers/    # Стратегии чанкинга
│   ├── embeddings/  # Embedding модели
│   ├── vector_stores/ # Векторные БД (FAISS, Qdrant)
│   ├── retrievers/  # Retrieval стратегии
│   ├── rerankers/   # Reranking стратегии
│   ├── routers/     # Query routing
│   ├── llm/         # LLM клиенты (Ollama)
│   ├── web_search/  # Web search (DuckDuckGo)
│   ├── evaluation/  # Evaluation метрики
│   ├── prompts/     # Промпты (Jinja2 шаблоны)
│   ├── monitoring/  # Логирование и метрики
│   └── workflows/   # LangGraph workflows
└── interfaces/      # Слой 4: Interfaces (API, UI)
    ├── api/         # FastAPI endpoints
    └── ui/          # Streamlit UI
```

## Правила работы

### Направление зависимостей

```
Interfaces → Application → Domain ← Infrastructure
```

- **Domain** — НЕ зависит ни от чего
- **Application** — зависит только от Domain
- **Infrastructure** — реализует порты из Domain
- **Interfaces** — зависит от Application

### Использование Protocol для абстракций

Все интерфейсы определяются через `typing.Protocol` (structural subtyping):

```python
from typing import Protocol, List

class Retriever(Protocol):
    async def retrieve(self, query: Query, top_k: int = 5) -> List[Tuple[Document, float]]: ...
```

### Конфигурация

Все настройки через Pydantic Settings + `.env` файл:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    # ...
```

### Промпты

Все промпты хранятся в `infrastructure/prompts/templates/` как Jinja2 шаблоны. НЕ хардкодить промпты в коде.

### Тестирование

- Unit тесты: `tests/unit/`
- Integration тесты: `tests/integration/`
- Quality тесты: `tests/evaluation/`

### Код стайл

- Python 3.10+
- Type hints везде
- Async/await для I/O операций
- Ruff для линтинга
- НЕ добавлять комментарии если не просят

## Ключевые технологии

- **LLM**: Ollama (llama3.2:3b-instruct-fp16 / gemma3:1b)
- **Embeddings**: HuggingFace (intfloat/multilingual-e5-large)
- **Vector Store**: FAISS / Qdrant
- **UI**: FastAPI + Streamlit
- **Конфигурация**: Pydantic Settings + YAML
- **Промпты**: Jinja2

## Типичные ошибки (чего НЕ делать)

1. **Нет hardcode** — все параметры через конфиг
2. **Нет pickle** — не использовать `allow_dangerous_deserialization=True` без необходимости
3. **Нет синхронного API** — везде async/await
4. **Нет монолита** — каждый компонент в отдельном файле
5. **Нет зависимости от конкретных библиотек** — использовать Protocol для абстракций

## Команды

```bash
# Установка
make install

# Запуск Ollama
make ollama-start
make ollama-pull MODEL=llama3.2:3b

# Запуск API
make run-api

# Запуск UI
make run-ui

# Тесты
make test

# Линтинг
make lint
```

## Файлы которые НЕ нужно менять

- `Local_RAG_Agent_01/` — старый прототип (в .gitignore)
- `.gitignore` — не трогать без необходимости
