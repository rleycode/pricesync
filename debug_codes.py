#!/usr/bin/env python3
"""
Скрипт для отладки соответствия кодов между GrandLine и OpenCart
"""

import os
import sys
from dotenv import load_dotenv
from src.database_updater import DatabaseUpdater
from src.grandline_client import GrandLineClient
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_codes():
    """Отладка соответствия кодов"""
    
    load_dotenv()
    
    print("=== ОТЛАДКА КОДОВ ТОВАРОВ ===\n")
    
    # 1. Подключаемся к БД
    db_updater = DatabaseUpdater()
    if not db_updater.connect():
        print("❌ Ошибка подключения к БД")
        return False
    
    try:
        cursor = db_updater.connection.cursor()
        
        # 2. Показываем примеры кодов из oc_product
        print("1. Примеры кодов model в oc_product (первые 10):")
        cursor.execute("SELECT model FROM oc_product WHERE model IS NOT NULL LIMIT 10")
        db_codes = cursor.fetchall()
        
        for i, (code,) in enumerate(db_codes, 1):
            print(f"  {i}. {code}")
        
        # 3. Получаем данные из GrandLine
        print(f"\n2. Получение данных из GrandLine API...")
        grandline_client = GrandLineClient()
        
        # Получаем цены (первые 10 для примера)
        prices = grandline_client.get_prices()
        if not prices:
            print("❌ Не удалось получить цены из GrandLine")
            return False
        
        print(f"Получено {len(prices)} цен из GrandLine")
        
        # Показываем первые nomenclature_id
        print(f"\n3. Примеры nomenclature_id из GrandLine (первые 10):")
        for i, price_item in enumerate(prices[:10], 1):
            nomenclature_id = price_item.get('nomenclature_id')
            price = price_item.get('price')
            print(f"  {i}. nomenclature_id: {nomenclature_id}, price: {price}")
        
        # 4. Получаем сопоставления nomenclature_id -> code_1c
        print(f"\n4. Получение сопоставлений nomenclature_id -> code_1c...")
        nomenclature_ids = [item['nomenclature_id'] for item in prices[:10]]  # Берем только первые 10
        nomenclatures = grandline_client.get_nomenclatures(nomenclature_ids)
        
        print(f"Получено {len(nomenclatures)} сопоставлений")
        
        # Показываем примеры сопоставлений
        print(f"\n5. Примеры сопоставлений nomenclature_id -> code_1c (первые 10):")
        count = 0
        for nomenclature_id, code_1c in nomenclatures.items():
            if count >= 10:
                break
            print(f"  {count + 1}. {nomenclature_id} -> {code_1c}")
            count += 1
        
        # 5. Проверяем есть ли эти code_1c в базе
        print(f"\n6. Проверка наличия code_1c в oc_product:")
        found_count = 0
        not_found_codes = []
        
        for nomenclature_id, code_1c in list(nomenclatures.items())[:10]:
            cursor.execute("SELECT COUNT(*) FROM oc_product WHERE model = %s", (code_1c,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                found_count += 1
                print(f"  ✅ {code_1c} найден в БД")
            else:
                not_found_codes.append(code_1c)
                print(f"  ❌ {code_1c} НЕ найден в БД")
        
        print(f"\nИз 10 проверенных кодов найдено в БД: {found_count}")
        
        # 6. Проверяем форматы кодов
        print(f"\n7. Анализ форматов кодов:")
        
        # Коды из БД
        cursor.execute("SELECT model FROM oc_product WHERE model IS NOT NULL LIMIT 5")
        db_sample = [row[0] for row in cursor.fetchall()]
        print(f"  Примеры кодов из БД: {db_sample}")
        
        # Коды из GrandLine
        gl_sample = list(nomenclatures.values())[:5]
        print(f"  Примеры кодов из GrandLine: {gl_sample}")
        
        # 7. Поиск похожих кодов
        if not_found_codes:
            print(f"\n8. Поиск похожих кодов для {not_found_codes[0]}:")
            search_code = not_found_codes[0]
            
            # Поиск с LIKE
            cursor.execute("SELECT model FROM oc_product WHERE model LIKE %s LIMIT 5", (f"%{search_code}%",))
            similar = cursor.fetchall()
            
            if similar:
                print(f"  Похожие коды в БД:")
                for code, in similar:
                    print(f"    - {code}")
            else:
                print(f"  Похожих кодов не найдено")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отладке: {e}")
        return False
    finally:
        db_updater.disconnect()

if __name__ == "__main__":
    debug_codes()
