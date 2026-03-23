# === CONFIG ===
# Load .env file
include .env
export

PYTHON = python3
OLLAMA_CONTAINER = ollama-docker
API_PORT ?= 8000
UI_PORT ?= 8501
OLLAMA_PORT ?= 11434

# Colors
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
CYAN = \033[0;36m
NC = \033[0m

.PHONY: help install \
        start stop restart status \
        start-api stop-api restart-api \
        start-ui stop-ui restart-ui \
        ollama-start ollama-stop \
        test lint index-docs logs \
        docker-up docker-down clean

# === HELP ===
help: ## Показать справку
	@echo "$(CYAN)RAG Document Search$(NC)"
	@echo ""
	@echo "$(YELLOW)Основное:$(NC)"
	@echo "  $(GREEN)make start$(NC)     — Запустить все сервисы"
	@echo "  $(GREEN)make stop$(NC)      — Остановить все сервисы"
	@echo "  $(GREEN)make restart$(NC)   — Перезапустить"
	@echo "  $(GREEN)make status$(NC)    — Статус системы"
	@echo ""
	@echo "$(YELLOW)Сервисы:$(NC)"
	@echo "  $(GREEN)make start-api$(NC) — Запустить API"
	@echo "  $(GREEN)make start-ui$(NC)  — Запустить UI"
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@echo "  $(GREEN)make docker-up$(NC)   — Запустить через Docker"
	@echo "  $(GREEN)make docker-down$(NC) — Остановить Docker"
	@echo ""

# === SETUP ===
install: ## Установить зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	$(PYTHON) -m pip install --upgrade pip --quiet
	$(PYTHON) -m pip install -r requirements.txt --quiet
	@mkdir -p logs data/documents
	@echo "$(GREEN)✓ Готово$(NC)"

# === OLLAMA ===
ollama-start: ## Запустить Ollama
	@docker start $(OLLAMA_CONTAINER) 2>/dev/null || \
		docker run -d --gpus=all -p 11434:11434 -v ollama:/root/.ollama --name $(OLLAMA_CONTAINER) ollama/ollama
	@echo "$(GREEN)✓ Ollama запущен$(NC)"

ollama-stop: ## Остановить Ollama
	@docker stop $(OLLAMA_CONTAINER) 2>/dev/null; docker rm $(OLLAMA_CONTAINER) 2>/dev/null; true
	@echo "$(GREEN)✓ Ollama остановлен$(NC)"

# === API ===
start-api: ## Запустить API
	@if curl -s http://localhost:$(API_PORT)/api/v1/health > /dev/null 2>&1; then \
		echo "$(YELLOW)API уже запущен$(NC)"; \
	else \
		echo "$(GREEN)Запуск API...$(NC)"; \
		mkdir -p logs; \
		nohup $(PYTHON) main.py > logs/api.log 2>&1 & \
		sleep 8; \
		if curl -s http://localhost:$(API_PORT)/api/v1/health > /dev/null 2>&1; then \
			echo "$(GREEN)✓ API: http://localhost:$(API_PORT)$(NC)"; \
		else \
			echo "$(RED)✗ API не запустился$(NC)"; \
		fi; \
	fi

stop-api: ## Остановить API
	@ps aux | grep "python3 main.py" | grep -v grep | grep -v make | awk '{print $$2}' | xargs -r kill 2>/dev/null || true
	@echo "$(GREEN)✓ API остановлен$(NC)"

stop-ui: ## Остановить UI
	@ps aux | grep "streamlit run" | grep -v grep | grep -v make | awk '{print $$2}' | xargs -r kill 2>/dev/null || true
	@echo "$(GREEN)✓ UI остановлен$(NC)"

start-ui: ## Запустить UI
	@if curl -s http://localhost:$(UI_PORT)/_stcore/health > /dev/null 2>&1; then \
		echo "$(YELLOW)UI уже запущен$(NC)"; \
	else \
		echo "$(GREEN)Запуск UI...$(NC)"; \
		mkdir -p logs; \
		nohup $(PYTHON) -m streamlit run src/interfaces/ui/streamlit_app.py \
			--server.port $(UI_PORT) \
			--server.address 0.0.0.0 \
			--server.headless true \
			> logs/ui.log 2>&1 & \
		sleep 5; \
		if curl -s http://localhost:$(UI_PORT)/_stcore/health > /dev/null 2>&1; then \
			echo "$(GREEN)✓ UI: http://localhost:$(UI_PORT)$(NC)"; \
		else \
			echo "$(RED)✗ UI не запустился$(NC)"; \
		fi; \
	fi

restart-ui: stop-ui start-ui ## Перезапустить UI

# === ALL ===
start: ollama-start start-api start-ui ## Запустить все сервисы
	@echo ""
	@echo "$(CYAN)Система запущена:$(NC)"
	@echo "  UI:  $(GREEN)http://localhost:$(UI_PORT)$(NC)"
	@echo "  API: $(GREEN)http://localhost:$(API_PORT)$(NC)"
	@echo ""

stop: stop-ui stop-api ## Остановить все сервисы
	@echo "$(GREEN)✓ Все сервисы остановлены$(NC)"

restart: stop start ## Перезапустить все

status: ## Показать статус
	@echo "$(CYAN)=== RAG Document Search ===$(NC)"
	@echo ""
	@printf "$(YELLOW)Ollama:$(NC) "
	@if docker ps | grep -q $(OLLAMA_CONTAINER); then echo "$(GREEN)✓$(NC)"; else echo "$(RED)✗$(NC)"; fi
	@printf "$(YELLOW)API:$(NC)    "
	@if curl -s http://localhost:$(API_PORT)/api/v1/health > /dev/null 2>&1; then echo "$(GREEN)✓ http://localhost:$(API_PORT)$(NC)"; else echo "$(RED)✗$(NC)"; fi
	@printf "$(YELLOW)UI:$(NC)     "
	@if curl -s http://localhost:$(UI_PORT)/_stcore/health > /dev/null 2>&1; then echo "$(GREEN)✓ http://localhost:$(UI_PORT)$(NC)"; else echo "$(RED)✗$(NC)"; fi
	@echo ""

# === OTHER ===
logs: ## Показать логи
	@echo "$(CYAN)=== API ===$(NC)"
	@tail -20 logs/api.log 2>/dev/null || echo "Нет логов"
	@echo ""
	@echo "$(CYAN)=== UI ===$(NC)"
	@tail -10 logs/ui.log 2>/dev/null || echo "Нет логов"

test: ## Тесты
	$(PYTHON) -m pytest tests/ -v

index-docs: ## Индексировать документы
	@echo "$(GREEN)Индексация...$(NC)"
	$(PYTHON) -c "\
import asyncio; \
from src.infrastructure.config.settings import get_settings; \
from src.interfaces.api.dependencies import get_index_use_case; \
results = asyncio.run(get_index_use_case().index_from_directory(get_settings().pdf_dir)); \
[print(f'  ✓ {r[\"source\"]}: {r.get(\"chunks_count\",0)} chunks') for r in results if r.get('status')=='indexed']"
	@echo "$(GREEN)✓ Готово$(NC)"

# === DOCKER ===
docker-up: ## Запустить через Docker
	docker-compose up -d --build

docker-down: ## Остановить Docker
	docker-compose down

rebuild-api: ## Пересобрать API (с удалением старого image)
	@echo "$(YELLOW)Удаление старого API image...$(NC)"
	docker rmi rag-docs-search-api 2>/dev/null || true
	@echo "$(GREEN)Сборка нового API image (no-cache)...$(NC)"
	docker build --no-cache -t rag-docs-search-api -f docker/Dockerfile.api .
	@echo "$(GREEN)✓ API image пересобран$(NC)"

rebuild-ui: ## Пересобрать UI (с удалением старого image)
	@echo "$(YELLOW)Удаление старого UI image...$(NC)"
	docker rmi rag-docs-search-ui 2>/dev/null || true
	@echo "$(GREEN)Сборка нового UI image (no-cache)...$(NC)"
	docker build --no-cache -t rag-docs-search-ui -f docker/Dockerfile.ui .
	@echo "$(GREEN)✓ UI image пересобран$(NC)"

rebuild: rebuild-api rebuild-ui ## Пересобрать все образы
	@echo "$(GREEN)✓ Все образы пересобраны$(NC)"

redeploy: docker-down rebuild docker-up ## Остановить, пересобрать, запустить
	@echo "$(GREEN)✓ Система пересобрана и запущена$(NC)"

# === CLEAN ===
clean: ## Очистить логи
	rm -rf logs/*.log
	@echo "$(GREEN)✓ Очищено$(NC)"
