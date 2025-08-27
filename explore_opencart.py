#!/usr/bin/env python3
"""
Скрипт для исследования структуры OpenCart базы данных
"""

import os
import sys
from dotenv import load_dotenv
from src.database_updater import DatabaseUpdater
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def explore_opencart_db():
    """Исследование структуры OpenCart базы данных"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    print("=== ИССЛЕДОВАНИЕ OPENCART БАЗЫ ДАННЫХ ===\n")
    
    # Создаем подключение к БД
    db_updater = DatabaseUpdater()
    
    # Подключаемся
    if not db_updater.connect():
        print("❌ Ошибка подключения к БД")
        return False
    
    try:
        cursor = db_updater.connection.cursor()
        
        # 1. Исследуем таблицу oc_product
        print("1. Структура таблицы oc_product:")
        cursor.execute("DESCRIBE oc_product")
        columns = cursor.fetchall()
        
        print("  Поля таблицы oc_product:")
        for col in columns:
            field, type_, null, key, default, extra = col
            print(f"    - {field}: {type_} (NULL: {null}, Key: {key}, Default: {default})")
        
        # 2. Количество товаров
        print(f"\n2. Статистика таблицы oc_product:")
        cursor.execute("SELECT COUNT(*) FROM oc_product")
        total_count = cursor.fetchone()[0]
        print(f"  Общее количество товаров: {total_count}")
        
        # 3. Проверяем поля для синхронизации
        print(f"\n3. Анализ полей для синхронизации цен:")
        
        # Проверяем наличие поля model (часто используется как код товара)
        cursor.execute("SELECT COUNT(*) FROM oc_product WHERE model IS NOT NULL AND model != ''")
        model_count = cursor.fetchone()[0]
        print(f"  Товаров с заполненным model: {model_count}")
        
        # Проверяем наличие поля sku
        cursor.execute("SELECT COUNT(*) FROM oc_product WHERE sku IS NOT NULL AND sku != ''")
        sku_count = cursor.fetchone()[0]
        print(f"  Товаров с заполненным sku: {sku_count}")
        
        # Проверяем поле price
        cursor.execute("SELECT COUNT(*) FROM oc_product WHERE price IS NOT NULL AND price > 0")
        price_count = cursor.fetchone()[0]
        print(f"  Товаров с ценой: {price_count}")
        
        # 4. Примеры записей
        print(f"\n4. Примеры записей из oc_product (первые 5):")
        cursor.execute("""
            SELECT product_id, model, sku, price, quantity, status 
            FROM oc_product 
            WHERE model IS NOT NULL AND model != ''
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        if examples:
            print("  product_id | model | sku | price | quantity | status")
            print("  " + "-" * 60)
            for row in examples:
                print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
        else:
            print("  Записи с model не найдены")
        
        # 5. Исследуем связанные таблицы
        print(f"\n5. Связанные таблицы для товаров:")
        
        # oc_product_description - описания товаров
        cursor.execute("SELECT COUNT(*) FROM oc_product_description")
        desc_count = cursor.fetchone()[0]
        print(f"  oc_product_description: {desc_count} записей")
        
        # oc_product_special - специальные цены
        cursor.execute("SELECT COUNT(*) FROM oc_product_special")
        special_count = cursor.fetchone()[0]
        print(f"  oc_product_special: {special_count} записей (акционные цены)")
        
        # oc_product_discount - скидки
        cursor.execute("SELECT COUNT(*) FROM oc_product_discount")
        discount_count = cursor.fetchone()[0]
        print(f"  oc_product_discount: {discount_count} записей (скидки)")
        
        # 6. Проверяем структуру oc_product_special
        print(f"\n6. Структура таблицы oc_product_special (для акционных цен):")
        cursor.execute("DESCRIBE oc_product_special")
        special_columns = cursor.fetchall()
        
        for col in special_columns:
            field, type_, null, key, default, extra = col
            print(f"    - {field}: {type_}")
        
        # 7. Примеры специальных цен
        print(f"\n7. Примеры из oc_product_special:")
        cursor.execute("""
            SELECT ps.product_id, p.model, ps.price, ps.date_start, ps.date_end
            FROM oc_product_special ps
            JOIN oc_product p ON ps.product_id = p.product_id
            LIMIT 5
        """)
        
        special_examples = cursor.fetchall()
        if special_examples:
            print("  product_id | model | special_price | date_start | date_end")
            print("  " + "-" * 70)
            for row in special_examples:
                print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
        else:
            print("  Специальные цены не найдены")
        
        print(f"\n=== РЕКОМЕНДАЦИИ ===")
        print("Для синхронизации цен с GrandLine рекомендуется:")
        print("1. Использовать таблицу: oc_product")
        print("2. Поле для поиска товара: model или sku (в зависимости от того, где хранится код 1С)")
        print("3. Поле для обновления цены: price")
        print("4. Дополнительно можно использовать oc_product_special для акционных цен")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при исследовании БД: {e}")
        return False
    finally:
        db_updater.disconnect()

if __name__ == "__main__":
    explore_opencart_db()
