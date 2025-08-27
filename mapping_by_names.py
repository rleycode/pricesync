#!/usr/bin/env python3
"""
Сопоставление товаров по названиям между GrandLine и OpenCart
"""

import os
import sys
from dotenv import load_dotenv
from src.database_updater import DatabaseUpdater
from src.grandline_client import GrandLineClient
import logging
from difflib import SequenceMatcher
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_name(name):
    """Очистка названия для лучшего сравнения"""
    if not name:
        return ""
    
    # Приводим к нижнему регистру
    name = name.lower()
    
    # Убираем лишние пробелы и символы
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Убираем общие слова
    stop_words = ['товар', 'изделие', 'продукт', 'материал', 'деталь']
    words = name.split()
    words = [w for w in words if w not in stop_words]
    
    return ' '.join(words)

def name_similarity(name1, name2):
    """Вычисляет схожесть названий"""
    clean1 = clean_name(name1)
    clean2 = clean_name(name2)
    
    if not clean1 or not clean2:
        return 0
    
    # Базовая схожесть
    base_similarity = SequenceMatcher(None, clean1, clean2).ratio()
    
    # Бонус за совпадающие ключевые слова
    words1 = set(clean1.split())
    words2 = set(clean2.split())
    
    if words1 and words2:
        common_words = words1.intersection(words2)
        word_bonus = len(common_words) / max(len(words1), len(words2))
        
        # Комбинируем базовую схожесть и бонус за слова
        final_similarity = (base_similarity * 0.7) + (word_bonus * 0.3)
    else:
        final_similarity = base_similarity
    
    return min(final_similarity, 1.0)

def get_grandline_products():
    """Получает товары из GrandLine с названиями"""
    grandline_client = GrandLineClient()
    
    try:
        # Получаем цены
        prices = grandline_client.get_prices()
        if not prices:
            return []
        
        print(f"Получено {len(prices)} позиций из GrandLine")
        
        # Получаем номенклатуры с названиями (ограничиваем до 500 для тестирования)
        test_nomenclature_ids = [item['nomenclature_id'] for item in prices[:500]]
        nomenclatures = grandline_client.get_nomenclatures_with_names(test_nomenclature_ids)
        
        # Формируем список товаров с ценами, кодами и названиями
        products = []
        for price_item in prices[:500]:
            nomenclature_id = price_item['nomenclature_id']
            if nomenclature_id in nomenclatures:
                nomenclature_info = nomenclatures[nomenclature_id]
                
                products.append({
                    'nomenclature_id': nomenclature_id,
                    'code_1c': nomenclature_info['code_1c'],
                    'price': price_item['price'],
                    'name': nomenclature_info['name']
                })
        
        return products
        
    except Exception as e:
        logger.error(f"Ошибка получения товаров из GrandLine: {e}")
        return []

def get_opencart_products():
    """Получает товары из OpenCart с названиями"""
    db_updater = DatabaseUpdater()
    if not db_updater.connect():
        return []
    
    try:
        cursor = db_updater.connection.cursor()
        
        # Получаем товары с названиями из oc_product_description
        cursor.execute("""
            SELECT p.product_id, p.model, p.sku, p.price, pd.name
            FROM oc_product p
            LEFT JOIN oc_product_description pd ON p.product_id = pd.product_id
            WHERE p.model IS NOT NULL AND p.model != ''
            AND pd.name IS NOT NULL AND pd.name != ''
            AND pd.language_id = 1
            LIMIT 1000
        """)
        
        products = []
        for row in cursor.fetchall():
            product_id, model, sku, price, name = row
            products.append({
                'product_id': product_id,
                'model': model,
                'sku': sku,
                'price': price,
                'name': name
            })
        
        return products
        
    except Exception as e:
        logger.error(f"Ошибка получения товаров из OpenCart: {e}")
        return []
    finally:
        db_updater.disconnect()

def find_matches_by_names(grandline_products, opencart_products, min_similarity=0.7):
    """Находит соответствия по названиям"""
    matches = []
    
    print(f"Поиск соответствий между {len(grandline_products)} товарами GrandLine и {len(opencart_products)} товарами OpenCart...")
    
    for i, gl_product in enumerate(grandline_products):
        if i % 50 == 0:
            print(f"Обработано {i}/{len(grandline_products)} товаров...")
        
        best_match = None
        best_score = 0
        
        for oc_product in opencart_products:
            similarity = name_similarity(gl_product['name'], oc_product['name'])
            
            if similarity > best_score and similarity >= min_similarity:
                best_match = oc_product
                best_score = similarity
        
        if best_match:
            matches.append({
                'grandline_code': gl_product['code_1c'],
                'grandline_name': gl_product['name'],
                'opencart_model': best_match['model'],
                'opencart_name': best_match['name'],
                'similarity': best_score,
                'product_id': best_match['product_id']
            })
    
    return matches

def mapping_by_names():
    """Основная функция сопоставления по названиям"""
    
    load_dotenv()
    
    print("=== СОПОСТАВЛЕНИЕ ПО НАЗВАНИЯМ ТОВАРОВ ===\n")
    
    # 1. Получаем товары из GrandLine
    print("1. Получение товаров из GrandLine...")
    grandline_products = get_grandline_products()
    
    if not grandline_products:
        print("❌ Не удалось получить товары из GrandLine")
        return False
    
    print(f"Получено {len(grandline_products)} товаров из GrandLine")
    
    # 2. Получаем товары из OpenCart
    print("\n2. Получение товаров из OpenCart...")
    opencart_products = get_opencart_products()
    
    if not opencart_products:
        print("❌ Не удалось получить товары из OpenCart")
        return False
    
    print(f"Получено {len(opencart_products)} товаров из OpenCart")
    
    # 3. Показываем примеры названий
    print(f"\n3. Примеры названий товаров:")
    print(f"GrandLine:")
    for product in grandline_products[:5]:
        print(f"  {product['code_1c']}: {product['name']}")
    
    print(f"\nOpenCart:")
    for product in opencart_products[:5]:
        print(f"  {product['model']}: {product['name']}")
    
    # 4. Поиск соответствий
    print(f"\n4. Поиск соответствий по названиям...")
    matches = find_matches_by_names(grandline_products, opencart_products, min_similarity=0.7)
    
    print(f"Найдено {len(matches)} соответствий")
    
    # 5. Показываем лучшие совпадения
    if matches:
        print(f"\n5. Лучшие совпадения:")
        sorted_matches = sorted(matches, key=lambda x: x['similarity'], reverse=True)
        
        for i, match in enumerate(sorted_matches[:10]):
            print(f"  {i+1}. Схожесть: {match['similarity']:.2f}")
            print(f"     GrandLine: {match['grandline_code']} - {match['grandline_name']}")
            print(f"     OpenCart:  {match['opencart_model']} - {match['opencart_name']}")
            print()
    
    # 6. Создание таблицы соответствий
    if matches:
        print(f"6. Создание таблицы соответствий...")
        
        db_updater = DatabaseUpdater()
        if db_updater.connect():
            try:
                cursor = db_updater.connection.cursor()
                
                # Создаем таблицу если не существует
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS oc_grandline_mapping (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        grandline_code VARCHAR(50) NOT NULL,
                        opencart_model VARCHAR(64) NOT NULL,
                        similarity_score DECIMAL(3,2),
                        mapping_method VARCHAR(20),
                        grandline_name TEXT,
                        opencart_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE KEY unique_grandline_code (grandline_code),
                        KEY idx_opencart_model (opencart_model)
                    )
                """)
                
                # Очищаем старые данные
                cursor.execute("DELETE FROM oc_grandline_mapping")
                
                # Вставляем соответствия с высокой схожестью
                high_confidence = [m for m in matches if m['similarity'] >= 0.8]
                
                for match in high_confidence:
                    cursor.execute("""
                        INSERT INTO oc_grandline_mapping 
                        (grandline_code, opencart_model, similarity_score, mapping_method, grandline_name, opencart_name) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        match['grandline_code'],
                        match['opencart_model'],
                        match['similarity'],
                        'name_similarity',
                        match['grandline_name'],
                        match['opencart_name']
                    ))
                
                db_updater.connection.commit()
                print(f"✅ Создано {len(high_confidence)} соответствий с высокой уверенностью (≥80%)")
                
            except Exception as e:
                print(f"❌ Ошибка создания таблицы: {e}")
            finally:
                db_updater.disconnect()
    
    # 7. Статистика
    total_gl = len(grandline_products)
    high_confidence = len([m for m in matches if m['similarity'] >= 0.8])
    coverage = (high_confidence / total_gl) * 100 if total_gl > 0 else 0
    
    print(f"\n=== РЕЗУЛЬТАТЫ ===")
    print(f"Всего товаров GrandLine: {total_gl}")
    print(f"Сопоставлено с высокой уверенностью: {high_confidence}")
    print(f"Покрытие: {coverage:.1f}%")
    
    return True

if __name__ == "__main__":
    mapping_by_names()
