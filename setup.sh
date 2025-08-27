#!/bin/bash

# Скрипт для настройки окружения PriceSync

echo "🚀 Настройка системы PriceSync..."

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация окружения и установка зависимостей
echo "Установка зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Создание необходимых директорий
echo "Создание директорий..."
mkdir -p downloads
mkdir -p logs

# Копирование примера конфигурации
if [ ! -f ".env" ]; then
    echo "Создание файла конфигурации..."
    cp .env.example .env
    echo "⚠️  Не забудьте отредактировать файл .env с вашими настройками!"
fi

# Проверка установки Chrome/Chromium для Selenium
if command -v google-chrome &> /dev/null; then
    echo "✅ Google Chrome найден"
elif command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium найден"
else
    echo "⚠️  Chrome/Chromium не найден. Установите для работы с Металлпрофиль:"
    echo "   sudo apt-get install chromium-browser"
    echo "   или"
    echo "   sudo apt-get install google-chrome-stable"
fi

# Проверка ChromeDriver
if command -v chromedriver &> /dev/null; then
    echo "✅ ChromeDriver найден"
else
    echo "⚠️  ChromeDriver не найден. Установите:"
    echo "   sudo apt-get install chromium-chromedriver"
fi

echo ""
echo "🎉 Настройка завершена!"
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте .env файл с вашими API ключами"
echo "2. Запустите тест: source venv/bin/activate && python main.py --mode test"
echo "3. Запустите синхронизацию: python main.py --mode once"
echo ""
