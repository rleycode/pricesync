FROM python:3.12-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY requirements.txt .
COPY src/ ./src/
COPY main.py .
COPY config.py .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Создание необходимых директорий
RUN mkdir -p downloads logs

# Настройка переменных окружения для Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium

# Создание пользователя для безопасности
RUN useradd -m -u 1000 pricesync && \
    chown -R pricesync:pricesync /app
USER pricesync

# Точка входа
ENTRYPOINT ["python", "main.py"]
