# 🚀 Руководство по развертыванию PriceSync

## Варианты развертывания

### 1. Локальная установка

#### Быстрая установка
```bash
# Клонирование и настройка
git clone <your-repo> pricesync
cd pricesync
./setup.sh
```

#### Ручная установка
```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Установка Chrome/ChromeDriver
./scripts/install_chrome.sh

# Настройка конфигурации
cp .env.example .env
# Отредактируйте .env файл
```

### 2. Docker развертывание

#### Сборка и запуск
```bash
# Планировщик (постоянная работа)
docker-compose up -d pricesync

# Разовый запуск
docker-compose --profile manual run --rm pricesync-once

# Просмотр логов
docker-compose logs -f pricesync
```

#### Управление контейнерами
```bash
# Остановка
docker-compose down

# Обновление
docker-compose pull
docker-compose up -d --force-recreate

# Очистка
docker-compose down -v
docker system prune -f
```

### 3. Системный сервис (systemd)

#### Создание сервиса
```bash
sudo tee /etc/systemd/system/pricesync.service > /dev/null <<EOF
[Unit]
Description=PriceSync Service
After=network.target

[Service]
Type=simple
User=pricesync
WorkingDirectory=/opt/pricesync
Environment=PATH=/opt/pricesync/venv/bin
ExecStart=/opt/pricesync/venv/bin/python main.py --mode schedule
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Управление сервисом
```bash
# Запуск
sudo systemctl enable pricesync
sudo systemctl start pricesync

# Статус
sudo systemctl status pricesync

# Логи
sudo journalctl -u pricesync -f

# Остановка
sudo systemctl stop pricesync
```

## Настройка окружения

### Системные требования
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Python**: 3.8+
- **RAM**: минимум 1GB, рекомендуется 2GB
- **Диск**: 2GB свободного места
- **Сеть**: доступ к внешним API

### Зависимости системы
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip
sudo apt-get install -y chromium-browser chromium-chromedriver
sudo apt-get install -y curl wget unzip

# CentOS/RHEL
sudo yum install -y python3 python3-pip
sudo yum install -y chromium chromedriver
```

## Конфигурация

### Обязательные настройки
```env
# GrandLine API
GRANDLINE_API_KEY=your_api_key_here
GRANDLINE_BRANCH_ID=your_branch_id
GRANDLINE_AGREEMENT_ID=your_agreement_id

# Металлпрофиль
METALLPROFIL_LOGIN=your_login
METALLPROFIL_PASSWORD=your_password

# Ваш сайт
WEBSITE_API_URL=https://your-site.com/api
WEBSITE_API_KEY=your_api_key
```

### Дополнительные настройки
```env
# Планировщик
SYNC_SCHEDULE_TIME=09:00

# Браузер
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30

# Пути
DOWNLOAD_DIR=/opt/pricesync/downloads
LOG_DIR=/opt/pricesync/logs
```

## Автоматизация

### Cron (альтернатива планировщику)
```bash
# Настройка cron
./scripts/cron_setup.sh

# Ручное добавление
crontab -e
# Добавить: 0 9 * * * /path/to/pricesync/run_sync.sh
```

### Мониторинг
```bash
# Проверка статуса
python main.py --mode test

# Просмотр логов
tail -f logs/pricesync.log
tail -f logs/errors.log

# Статистика
grep "успешно" logs/pricesync.log | wc -l
grep "ERROR" logs/pricesync.log | tail -10
```

## Безопасность

### Файловые права
```bash
# Настройка прав доступа
chmod 600 .env
chmod 755 *.sh
chmod -R 755 src/
chown -R pricesync:pricesync /opt/pricesync
```

### Сетевая безопасность
- Используйте HTTPS для всех API соединений
- Ограничьте доступ к серверу через firewall
- Регулярно обновляйте зависимости

### Резервное копирование
```bash
# Создание бэкапа конфигурации
tar -czf pricesync-backup-$(date +%Y%m%d).tar.gz \
    .env config.py logs/ downloads/

# Восстановление
tar -xzf pricesync-backup-YYYYMMDD.tar.gz
```

## Устранение неполадок

### Частые проблемы

#### 1. Ошибка ChromeDriver
```bash
# Проверка версий
google-chrome --version
chromedriver --version

# Переустановка
sudo apt-get remove chromium-chromedriver
./scripts/install_chrome.sh
```

#### 2. Ошибки API
```bash
# Проверка соединения
curl -H "Authorization: Bearer $API_KEY" $API_URL/health

# Тест через приложение
python main.py --mode test
```

#### 3. Проблемы с правами
```bash
# Исправление прав
sudo chown -R $USER:$USER .
chmod +x setup.sh scripts/*.sh
```

#### 4. Нехватка памяти
```bash
# Мониторинг памяти
free -h
ps aux | grep python

# Настройка swap (если нужно)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Логи и диагностика
```bash
# Включение отладки
export LOG_LEVEL=DEBUG
python main.py --mode once

# Анализ производительности
python -m cProfile main.py --mode once

# Проверка сетевых соединений
netstat -tulpn | grep python
```

## Масштабирование

### Горизонтальное масштабирование
- Разделение источников по разным серверам
- Использование очередей задач (Celery + Redis)
- Балансировка нагрузки

### Вертикальное масштабирование
- Увеличение ресурсов сервера
- Оптимизация настроек браузера
- Кэширование результатов

### Мониторинг производительности
```bash
# Установка мониторинга
pip install psutil
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'RAM: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"
```
