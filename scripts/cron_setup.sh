#!/bin/bash


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Настройка cron для автоматического запуска PriceSync..."

# Создание скрипта запуска
cat > "$PROJECT_DIR/run_sync.sh" << EOF
#!/bin/bash
cd "$PROJECT_DIR"
source venv/bin/activate
python main.py --mode once >> logs/cron.log 2>&1
EOF

chmod +x "$PROJECT_DIR/run_sync.sh"

# Добавление задачи в cron (ежедневно в 9:00)
CRON_JOB="0 9 * * * $PROJECT_DIR/run_sync.sh"

# Проверка, существует ли уже задача
if crontab -l 2>/dev/null | grep -q "$PROJECT_DIR/run_sync.sh"; then
    echo "Cron задача уже существует"
else
    # Добавление новой задачи
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Cron задача добавлена: ежедневно в 9:00"
fi

# Создание логов для cron
mkdir -p "$PROJECT_DIR/logs"
touch "$PROJECT_DIR/logs/cron.log"

echo ""
echo "Текущие cron задачи:"
crontab -l | grep -E "(pricesync|run_sync)" || echo "Нет задач PriceSync"

echo ""
echo "Настройка cron завершена!"
echo ""
echo "Для изменения времени запуска отредактируйте cron:"
echo "crontab -e"
echo ""
echo "Формат времени cron: минута час день месяц день_недели"
echo "Примеры:"
echo "0 9 * * *     - каждый день в 9:00"
echo "0 */6 * * *   - каждые 6 часов"
echo "0 9,15 * * *  - в 9:00 и 15:00"
