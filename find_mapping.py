#!/usr/bin/env python3
"""
Скрипт для поиска связи между кодами GrandLine и OpenCart
"""

import os
import sys
from dotenv import load_dotenv
from src.database_updater import DatabaseUpdater
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_mapping():
    """Поиск связи между кодами"""
    
    load_dotenv()
    
    print("=== ПОИСК СВЯЗИ МЕЖДУ КОДАМИ ===\n")
    
    # Подключаемся к БД
    db_updater = DatabaseUpdater()
    if not db_updater.connect():
        print("❌ Ошибка подключения к БД")
        return False
    
    try:
        cursor = db_updater.connection.cursor()
        
        # Коды из GrandLine для поиска
        grandline_codes = ['562013', '551666', '529051', '529053', '482907']
        
        print("1. Поиск кодов GrandLine в различных полях oc_product:")
        
        # Проверяем все возможные поля с кодами
        fields_to_check = ['model', 'sku', 'upc', 'ean', 'jan', 'isbn', 'mpn']
        
        for field in fields_to_check:
            print(f"\n   Поиск в поле '{field}':")
            found_any = False
            
            for code in grandline_codes:
                cursor.execute(f"SELECT product_id, {field} FROM oc_product WHERE {field} = %s", (code,))
                result = cursor.fetchone()
                
                if result:
                    print(f"     ✅ {code} найден: product_id={result[0]}")
                    found_any = True
            
            if not found_any:
                print(f"     ❌ Ни один код не найден в поле '{field}'")
        
        # 2. Проверяем связанные таблицы
        print(f"\n2. Поиск в связанных таблицах:")
        
        # oc_product_attribute - атрибуты товаров
        print(f"\n   Поиск в oc_product_attribute:")
        for code in grandline_codes[:3]:  # Проверяем первые 3
            cursor.execute("""
                SELECT pa.product_id, pa.text, ad.name 
                FROM oc_product_attribute pa
                JOIN oc_attribute_description ad ON pa.attribute_id = ad.attribute_id
                WHERE pa.text = %s
                LIMIT 5
            """, (code,))
            results = cursor.fetchall()
            
            if results:
                print(f"     ✅ {code} найден в атрибутах:")
                for product_id, text, attr_name in results:
                    print(f"       product_id={product_id}, атрибут='{attr_name}', значение='{text}'")
            else:
                print(f"     ❌ {code} не найден в атрибутах")
        
        # 3. Поиск частичных совпадений
        print(f"\n3. Поиск частичных совпадений:")
        
        for code in grandline_codes[:2]:  # Проверяем первые 2
            print(f"\n   Поиск частичных совпадений для {code}:")
            
            # Поиск по последним цифрам
            last_digits = code[-4:]  # Последние 4 цифры
            cursor.execute("SELECT model, sku FROM oc_product WHERE model LIKE %s OR sku LIKE %s LIMIT 5", 
                          (f"%{last_digits}", f"%{last_digits}"))
            results = cursor.fetchall()
            
            if results:
                print(f"     Товары с окончанием '{last_digits}':")
                for model, sku in results:
                    print(f"       model={model}, sku={sku}")
            
            # Поиск по первым цифрам
            first_digits = code[:3]  # Первые 3 цифры
            cursor.execute("SELECT model, sku FROM oc_product WHERE model LIKE %s OR sku LIKE %s LIMIT 5", 
                          (f"{first_digits}%", f"{first_digits}%"))
            results = cursor.fetchall()
            
            if results:
                print(f"     Товары с началом '{first_digits}':")
                for model, sku in results:
                    print(f"       model={model}, sku={sku}")
        
        # 4. Проверяем есть ли поле с кодом 1С
        print(f"\n4. Поиск полей содержащих '1c' или 'code':")
        cursor.execute("DESCRIBE oc_product")
        columns = cursor.fetchall()
        
        relevant_fields = []
        for col in columns:
            field_name = col[0].lower()
            if '1c' in field_name or 'code' in field_name or 'external' in field_name:
                relevant_fields.append(col[0])
        
        if relevant_fields:
            print(f"   Найдены поля: {relevant_fields}")
            
            for field in relevant_fields:
                print(f"\n   Примеры значений в поле '{field}':")
                cursor.execute(f"SELECT {field} FROM oc_product WHERE {field} IS NOT NULL AND {field} != '' LIMIT 5")
                values = cursor.fetchall()
                
                for value, in values:
                    print(f"     {value}")
        else:
            print("   Поля с '1c' или 'code' не найдены")
        
        # 5. Проверяем поле suppler_code (если есть)
        print(f"\n5. Проверка поля suppler_code:")
        try:
            cursor.execute("SELECT suppler_code FROM oc_product WHERE suppler_code IS NOT NULL AND suppler_code != 0 LIMIT 10")
            suppler_codes = cursor.fetchall()
            
            if suppler_codes:
                print("   Примеры suppler_code:")
                for code, in suppler_codes:
                    print(f"     {code}")
                
                # Проверяем есть ли совпадения
                for gl_code in grandline_codes[:3]:
                    cursor.execute("SELECT product_id, model FROM oc_product WHERE suppler_code = %s", (gl_code,))
                    result = cursor.fetchone()
                    
                    if result:
                        print(f"   ✅ {gl_code} найден в suppler_code: product_id={result[0]}, model={result[1]}")
            else:
                print("   suppler_code пустой или не используется")
                
        except Exception as e:
            print(f"   Ошибка при проверке suppler_code: {e}")
        
        print(f"\n=== РЕКОМЕНДАЦИИ ===")
        print("Возможные варианты решения:")
        print("1. Найти таблицу соответствий кодов в OpenCart")
        print("2. Проверить настройки импорта из 1С в OpenCart")
        print("3. Использовать другое поле для связи (атрибуты, suppler_code)")
        print("4. Создать собственную таблицу соответствий")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        return False
    finally:
        db_updater.disconnect()

if __name__ == "__main__":
    find_mapping()
