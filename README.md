# PriceSync - Система автоматического обновления цен

Автоматическая система синхронизации цен с внешними источниками: GrandLine API и Металлпрофиль.

## 🎯 Основные возможности

- **GrandLine API интеграция**: Автоматическое получение актуальных цен через API
- **Металлпрофиль скрапинг**: Автоматический вход в личный кабинет и получение прайс-листов
- **PDF обработка**: Извлечение данных о товарах из PDF файлов
- **Автоматическое обновление**: Обновление цен на вашем сайте
- **Планировщик задач**: Автоматический запуск по расписанию
- **Логирование**: Подробное логирование всех операций

## 🏗️ Архитектура проекта

```
pricesync/
├── src/
│   ├── grandline_client.py     # Клиент для GrandLine API
│   ├── metallprofil_scraper.py # Веб-скрапер для Металлпрофиль
│   ├── pdf_processor.py        # Обработка PDF файлов
│   ├── website_updater.py      # Обновление цен на сайте
│   ├── scheduler.py            # Планировщик задач
│   └── logger.py               # Система логирования
├── main.py                     # Главный модуль
├── config.py                   # Конфигурация
├── requirements.txt            # Зависимости
└── .env.example               # Пример настроек
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка конфигурации

Скопируйте `.env.example` в `.env` и заполните необходимые параметры:

```bash
cp .env.example .env
```

Отредактируйте `.env` файл:

```env
# GrandLine API
GRANDLINE_API_KEY=your_api_key_here
GRANDLINE_BRANCH_ID=your_branch_id
GRANDLINE_AGREEMENT_ID=your_agreement_id

# Металлпрофиль
METALLPROFIL_LOGIN=your_login
METALLPROFIL_PASSWORD=your_password

# API вашего сайта
WEBSITE_API_URL=https://your-website.com/api
WEBSITE_API_KEY=your_website_api_key
```

### 3. Установка Chrome WebDriver

Для работы с Металлпрофиль необходим Chrome WebDriver:

```bash
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# или скачайте с https://chromedriver.chromium.org/
```

## 📋 Использование

### Проверка соединений

```bash
python main.py --mode test
```

### Однократная синхронизация

```bash
# Все источники
python main.py --mode once

# Только GrandLine
python main.py --mode once --source grandline

# Только Металлпрофиль
python main.py --mode once --source metallprofil
```

### Запуск планировщика

```bash
python main.py --mode schedule
```

## 🔄 Процесс синхронизации

### GrandLine

1. **Запрос к `/prices/`** - получение списка товаров с ценами
2. **Сопоставление nomenclature_id → code_1c** - через API `/nomenclatures/`
3. **Обновление цен** - отправка данных на ваш сайт

```json
[
  {"code_1c": "000261877", "price": "940.00"},
  {"code_1c": "000032375", "price": "1133.00"}
]
```

### Металлпрофиль

1. **Автоматический вход** - в личный кабинет через Selenium
2. **Скачивание PDF** - прайс-лист в заданную папку
3. **Обработка данных** - извлечение товаров и цен из PDF
4. **Фильтрация** - по толщине, типу покрытия и другим правилам

## ⚙️ Конфигурация

### Основные параметры

| Параметр | Описание | Значение по умолчанию |
|----------|----------|----------------------|
| `SYNC_SCHEDULE_TIME` | Время ежедневной синхронизации | `09:00` |
| `BROWSER_HEADLESS` | Запуск браузера в фоновом режиме | `True` |
| `BROWSER_TIMEOUT` | Таймаут браузера (сек) | `30` |
| `DOWNLOAD_DIR` | Директория для загрузок | `./downloads` |
| `LOG_DIR` | Директория для логов | `./logs` |

### Правила обработки PDF

```python
processing_rules = {
    'thickness_range': {'min': 0.4, 'max': 1.0},
    'coating_types': ['полиэстер', 'пурал'],
    'keywords': {
        'include': ['профнастил', 'металлочерепица'],
        'exclude': ['брак', 'б/у']
    }
}
```

## 📊 Логирование

Система создает несколько типов логов:

- `logs/pricesync.log` - основной лог (ротация 10MB)
- `logs/errors.log` - только ошибки (ротация 5MB)
- Консольный вывод для мониторинга

Уровни логирования:
- `DEBUG` - подробная информация
- `INFO` - основные события
- `WARNING` - предупреждения
- `ERROR` - ошибки

## 🔧 API интеграция

### GrandLine API

Основные эндпоинты:
- `GET /prices/` - получение цен
- `GET /nomenclatures/` - получение номенклатуры

### API вашего сайта

Ожидаемые эндпоинты:
- `PUT /products/{code_1c}/price` - обновление цены товара
- `PUT /products/prices/batch` - массовое обновление цен
- `GET /health` - проверка состояния API

## 🐛 Отладка

### Частые проблемы

1. **Ошибка WebDriver**
   ```bash
   # Проверьте установку Chrome/Chromium
   google-chrome --version
   chromedriver --version
   ```

2. **Ошибки API**
   ```bash
   # Проверьте соединения
   python main.py --mode test
   ```

3. **Проблемы с PDF**
   - Убедитесь, что файл не поврежден
   - Проверьте права доступа к директории загрузок

### Включение отладочного режима

```python
# В config.py
BROWSER_HEADLESS = False  # Показать браузер
LOG_LEVEL = 'DEBUG'       # Подробные логи
```

## 📈 Мониторинг

### Статистика синхронизации

```python
from main import PriceSyncManager

manager = PriceSyncManager()
results = manager.run_once()

print(f"GrandLine: {'✓' if results['grandline'] else '✗'}")
print(f"Металлпрофиль: {'✓' if results['metallprofil'] else '✗'}")
```

### Планировщик

```python
# Получение статуса планировщика
status = manager.scheduler.get_status()
print(f"Следующий запуск: {status['next_run']}")
```

## 🔒 Безопасность

- Храните API ключи в `.env` файле
- Не коммитьте `.env` в репозиторий
- Используйте HTTPS для API соединений
- Регулярно обновляйте зависимости

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте логи в `logs/`
2. Запустите тест соединений
3. Убедитесь в корректности настроек в `.env`

## 📝 Лицензия

Этот проект предназначен для внутреннего использования.
