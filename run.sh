#!/bin/bash
# Скрипт для запуска API и UI

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# Добавляем локальный pip в PATH
export PATH="$HOME/.local/bin:$PATH"

echo -e "${GREEN}=== RAG Document Search Launcher ===${NC}"
echo ""

# Проверяем Ollama
echo -e "${YELLOW}Проверка Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama доступен${NC}"
else
    echo -e "${RED}✗ Ollama недоступен${NC}"
    echo -e "${YELLOW}Запустите: docker start ollama-docker${NC}"
    exit 1
fi

# Убиваем старые процессы
echo -e "${YELLOW}Остановка старых процессов...${NC}"
pkill -f "python3 main.py" 2>/dev/null || true
pkill -f "streamlit run" 2>/dev/null || true
sleep 2

# Запускаем API
echo -e "${YELLOW}Запуск API на порту 8000...${NC}"
python3 main.py > logs/api.log 2>&1 &
API_PID=$!
echo "API PID: $API_PID"

# Ждём запуска API
echo -e "${YELLOW}Ожидание запуска API...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API запущен${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ API не запустился за 30 секунд${NC}"
        echo "Логи:"
        cat logs/api.log
        exit 1
    fi
done

# Запускаем UI
echo -e "${YELLOW}Запуск UI на порту 8501...${NC}"
streamlit run src/interfaces/ui/streamlit_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    > logs/ui.log 2>&1 &
UI_PID=$!
echo "UI PID: $UI_PID"

sleep 3

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Система запущена!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "API: ${GREEN}http://localhost:8000${NC}"
echo -e "UI:  ${GREEN}http://localhost:8501${NC}"
echo -e "Docs:${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "Для остановки нажмите Ctrl+C"
echo ""

# Обработка Ctrl+C
trap "echo ''; echo 'Остановка...'; kill $API_PID $UI_PID 2>/dev/null; exit 0" INT TERM

# Ждём
wait
