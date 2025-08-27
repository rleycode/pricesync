#!/usr/bin/env python3
"""
Скрипт для исследования структуры базы данных
"""

import os
import sys
from dotenv import load_dotenv
from src.database_updater import DatabaseUpdater
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def explore_database():
    """Исследование структуры базы данных"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    print("=== ИССЛЕДОВАНИЕ БАЗЫ ДАННЫХ ===\n")
    
    # Создаем подключение к БД
    db_updater = DatabaseUpdater()
    
    # Тестируем подключение
    print("1. Тестирование подключения к БД...")
    if not db_updater.test_connection():
        print("❌ Не удалось подключиться к базе данных!")
        print("Проверьте настройки в .env файле:")
        print(f"  DATABASE_TYPE: {db_updater.db_type}")
        print(f"  DATABASE_HOST: {db_updater.db_host}")
        print(f"  DATABASE_PORT: {db_updater.db_port}")
        print(f"  DATABASE_NAME: {db_updater.db_name}")
        print(f"  DATABASE_USER: {db_updater.db_user}")
        return False
    
    print("✅ Подключение к БД успешно!")
    
    # Подключаемся для дальнейшего исследования
    if not db_updater.connect():
        print("❌ Ошибка подключения для исследования")
        return False
    
    try:
        cursor = db_updater.connection.cursor()
        
        # 2. Показываем список всех таблиц
        print("\n2. Список таблиц в базе данных:")
        if db_updater.db_type.lower() == 'mysql':
            cursor.execute("SHOW TABLES")
        elif db_updater.db_type.lower() == 'postgresql':
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        elif db_updater.db_type.lower() == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        tables = cursor.fetchall()
        if tables:
            for i, table in enumerate(tables, 1):
                table_name = table[0]
                print(f"  {i}. {table_name}")
        else:
            print("  Таблицы не найдены")
        
        # 3. Анализируем таблицу товаров OpenCart
        products_table = "oc_product"  # Основная таблица товаров в OpenCart
        print(f"\n3. Анализ таблицы товаров OpenCart: '{products_table}'")
        
        # Проверяем существование таблицы
        table_exists = False
        for table in tables:
            if table[0].lower() == products_table.lower():
                table_exists = True
                break
        
        if not table_exists:
            print(f"❌ Таблица '{products_table}' не найдена!")
            print("Доступные таблицы:")
            for table in tables:
                print(f"  - {table[0]}")
            return False
        
        print(f"✅ Таблица '{products_table}' найдена")
        
        # 4. Показываем структуру таблицы товаров
        print(f"\n4. Структура таблицы '{products_table}':")
        if db_updater.db_type.lower() == 'mysql':
            cursor.execute(f"DESCRIBE {products_table}")
        elif db_updater.db_type.lower() == 'postgresql':
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = '{products_table}'
            """)
        elif db_updater.db_type.lower() == 'sqlite':
            cursor.execute(f"PRAGMA table_info({products_table})")
        
        columns = cursor.fetchall()
        if columns:
            print("  Поля таблицы:")
            for col in columns:
                if db_updater.db_type.lower() == 'mysql':
                    field, type_, null, key, default, extra = col
                    print(f"    - {field}: {type_} (NULL: {null}, Key: {key}, Default: {default})")
                elif db_updater.db_type.lower() == 'postgresql':
                    field, type_, null, default = col
                    print(f"    - {field}: {type_} (NULL: {null}, Default: {default})")
                elif db_updater.db_type.lower() == 'sqlite':
                    cid, field, type_, null, default, pk = col
                    print(f"    - {field}: {type_} (NULL: {not null}, Default: {default}, PK: {pk})")
        
        # 5. Проверяем настроенные поля
        print(f"\n5. Проверка настроенных полей:")
        print(f"  Поле кода 1С: '{db_updater.code_field}'")
        print(f"  Поле цены: '{db_updater.price_field}'")
        
        # Проверяем существование полей
        column_names = []
        if db_updater.db_type.lower() == 'mysql':
            column_names = [col[0] for col in columns]
        elif db_updater.db_type.lower() == 'postgresql':
            column_names = [col[0] for col in columns]
        elif db_updater.db_type.lower() == 'sqlite':
            column_names = [col[1] for col in columns]
        
        code_field_exists = db_updater.code_field in column_names
        price_field_exists = db_updater.price_field in column_names
        
        print(f"  ✅ Поле '{db_updater.code_field}' {'найдено' if code_field_exists else '❌ НЕ НАЙДЕНО'}")
        print(f"  ✅ Поле '{db_updater.price_field}' {'найдено' if price_field_exists else '❌ НЕ НАЙДЕНО'}")
        
        # 6. Показываем количество записей
        print(f"\n6. Статистика таблицы '{products_table}':")
        cursor.execute(f"SELECT COUNT(*) FROM {products_table}")
        total_count = cursor.fetchone()[0]
        print(f"  Общее количество товаров: {total_count}")
        
        if code_field_exists:
            cursor.execute(f"SELECT COUNT(*) FROM {products_table} WHERE {db_updater.code_field} IS NOT NULL AND {db_updater.code_field} != ''")
            code_count = cursor.fetchone()[0]
            print(f"  Товаров с кодом 1С: {code_count}")
        
        if price_field_exists:
            cursor.execute(f"SELECT COUNT(*) FROM {products_table} WHERE {db_updater.price_field} IS NOT NULL AND {db_updater.price_field} > 0")
            price_count = cursor.fetchone()[0]
            print(f"  Товаров с ценой: {price_count}")
        
        # 7. Показываем примеры записей
        print(f"\n7. Примеры записей из таблицы (первые 5):")
        if code_field_exists and price_field_exists:
            cursor.execute(f"""
                SELECT {db_updater.code_field}, {db_updater.price_field}, 
                       CASE WHEN 'name' IN ({','.join([f"'{col}'" for col in column_names])}) THEN name ELSE 'N/A' END as name
                FROM {products_table} 
                WHERE {db_updater.code_field} IS NOT NULL 
                LIMIT 5
            """)
        else:
            cursor.execute(f"SELECT * FROM {products_table} LIMIT 5")
        
        examples = cursor.fetchall()
        if examples:
            for i, row in enumerate(examples, 1):
                print(f"    {i}. {row}")
        else:
            print("    Записи не найдены")
        
        print(f"\n=== ИССЛЕДОВАНИЕ ЗАВЕРШЕНО ===")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при исследовании БД: {e}")
        return False
    finally:
        db_updater.disconnect()

if __name__ == "__main__":
    explore_database()
