#!/usr/bin/env python3
"""
Автоматическое сопоставление кодов GrandLine и OpenCart
"""

import os
import sys
from dotenv import load_dotenv
from src.database_updater import DatabaseUpdater
from src.grandline_client import GrandLineClient
import logging
from difflib import SequenceMatcher

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def similarity(a, b):
    """Вычисляет схожесть двух строк"""
    return SequenceMatcher(None, a, b).ratio()

def find_best_matches(grandline_codes, opencart_codes, min_similarity=0.6):
    """
    Находит лучшие совпадения между кодами
    
    Args:
        grandline_codes: список кодов из GrandLine
        opencart_codes: список кодов из OpenCart
        min_similarity: минимальная схожесть для считания совпадением
    
    Returns:
        dict: {grandline_code: opencart_code}
    """
    matches = {}
    
    for gl_code in grandline_codes:
        best_match = None
        best_score = 0
        
        for oc_code in opencart_codes:
            # 1. Проверяем точное совпадение
            if gl_code == oc_code:
                best_match = oc_code
                best_score = 1.0
                break
            
            # 2. Проверяем совпадение окончаний (последние 4-6 цифр)
            if len(gl_code) >= 4 and len(oc_code) >= 4:
                gl_suffix = gl_code[-4:]
                oc_suffix = oc_code[-4:]
                if gl_suffix == oc_suffix:
                    score = 0.8  # Высокий приоритет для совпадения окончаний
                    if score > best_score:
                        best_match = oc_code
                        best_score = score
            
            # 3. Проверяем совпадение начал
            if len(gl_code) >= 3 and len(oc_code) >= 3:
                gl_prefix = gl_code[:3]
                oc_prefix = oc_code[:3]
                if gl_prefix == oc_prefix:
                    score = 0.7
                    if score > best_score:
                        best_match = oc_code
                        best_score = score
            
            # 4. Общая схожесть строк
            score = similarity(gl_code, oc_code)
            if score > best_score and score >= min_similarity:
                best_match = oc_code
                best_score = score
        
        if best_match and best_score >= min_similarity:
            matches[gl_code] = {
                'opencart_code': best_match,
                'similarity': best_score,
                'method': 'exact' if best_score == 1.0 else 
                         'suffix' if best_score == 0.8 else
                         'prefix' if best_score == 0.7 else 'similarity'
            }
    
    return matches

def auto_mapping():
    """Автоматическое сопоставление кодов"""
    
    load_dotenv()
    
    print("=== АВТОМАТИЧЕСКОЕ СОПОСТАВЛЕНИЕ КОДОВ ===\n")
    
    # 1. Получаем коды из GrandLine
    print("1. Получение кодов из GrandLine...")
    grandline_client = GrandLineClient()
    
    try:
        prices = grandline_client.get_prices()
        if not prices:
            print("❌ Не удалось получить цены из GrandLine")
            return False
        
        print(f"Получено {len(prices)} позиций из GrandLine")
        
        # Получаем первые 1000 для тестирования
        test_nomenclature_ids = [item['nomenclature_id'] for item in prices[:1000]]
        nomenclatures = grandline_client.get_nomenclatures(test_nomenclature_ids)
        
        grandline_codes = list(nomenclatures.values())
        print(f"Получено {len(grandline_codes)} кодов из GrandLine для анализа")
        
    except Exception as e:
        print(f"❌ Ошибка получения данных из GrandLine: {e}")
        return False
    
    # 2. Получаем коды из OpenCart
    print("\n2. Получение кодов из OpenCart...")
    db_updater = DatabaseUpdater()
    if not db_updater.connect():
        print("❌ Ошибка подключения к БД")
        return False
    
    try:
        cursor = db_updater.connection.cursor()
        cursor.execute("SELECT model FROM oc_product WHERE model IS NOT NULL AND model != ''")
        opencart_codes = [row[0] for row in cursor.fetchall()]
        print(f"Получено {len(opencart_codes)} кодов из OpenCart")
        
    except Exception as e:
        print(f"❌ Ошибка получения кодов из OpenCart: {e}")
        return False
    
    # 3. Автоматическое сопоставление
    print("\n3. Поиск совпадений...")
    matches = find_best_matches(grandline_codes, opencart_codes, min_similarity=0.6)
    
    print(f"Найдено {len(matches)} потенциальных совпадений")
    
    # 4. Анализ результатов
    print("\n4. Анализ найденных совпадений:")
    
    exact_matches = sum(1 for m in matches.values() if m['method'] == 'exact')
    suffix_matches = sum(1 for m in matches.values() if m['method'] == 'suffix')
    prefix_matches = sum(1 for m in matches.values() if m['method'] == 'prefix')
    similarity_matches = sum(1 for m in matches.values() if m['method'] == 'similarity')
    
    print(f"  Точные совпадения: {exact_matches}")
    print(f"  По окончанию: {suffix_matches}")
    print(f"  По началу: {prefix_matches}")
    print(f"  По схожести: {similarity_matches}")
    
    # 5. Показываем примеры лучших совпадений
    print(f"\n5. Примеры лучших совпадений:")
    
    sorted_matches = sorted(matches.items(), key=lambda x: x[1]['similarity'], reverse=True)
    
    for i, (gl_code, match_info) in enumerate(sorted_matches[:10]):
        oc_code = match_info['opencart_code']
        similarity_score = match_info['similarity']
        method = match_info['method']
        print(f"  {i+1}. {gl_code} → {oc_code} (схожесть: {similarity_score:.2f}, метод: {method})")
    
    # 6. Создание таблицы соответствий
    print(f"\n6. Создание таблицы соответствий...")
    
    try:
        # Создаем таблицу если не существует
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oc_grandline_mapping (
                id INT AUTO_INCREMENT PRIMARY KEY,
                grandline_code VARCHAR(50) NOT NULL,
                opencart_model VARCHAR(64) NOT NULL,
                similarity_score DECIMAL(3,2),
                mapping_method VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_grandline_code (grandline_code),
                KEY idx_opencart_model (opencart_model)
            )
        """)
        
        # Очищаем старые данные
        cursor.execute("DELETE FROM oc_grandline_mapping")
        
        # Вставляем новые соответствия
        high_confidence_matches = {k: v for k, v in matches.items() if v['similarity'] >= 0.8}
        
        for gl_code, match_info in high_confidence_matches.items():
            cursor.execute("""
                INSERT INTO oc_grandline_mapping 
                (grandline_code, opencart_model, similarity_score, mapping_method) 
                VALUES (%s, %s, %s, %s)
            """, (
                gl_code,
                match_info['opencart_code'],
                match_info['similarity'],
                match_info['method']
            ))
        
        db_updater.connection.commit()
        print(f"✅ Создано {len(high_confidence_matches)} соответствий с высокой уверенностью (≥80%)")
        
    except Exception as e:
        print(f"❌ Ошибка создания таблицы соответствий: {e}")
        return False
    
    # 7. Статистика покрытия
    total_gl_codes = len(grandline_codes)
    mapped_codes = len(high_confidence_matches)
    coverage = (mapped_codes / total_gl_codes) * 100 if total_gl_codes > 0 else 0
    
    print(f"\n=== РЕЗУЛЬТАТЫ ===")
    print(f"Всего кодов GrandLine: {total_gl_codes}")
    print(f"Сопоставлено автоматически: {mapped_codes}")
    print(f"Покрытие: {coverage:.1f}%")
    
    if coverage < 50:
        print(f"\n⚠️  РЕКОМЕНДАЦИИ:")
        print(f"Низкое покрытие может означать:")
        print(f"1. Разные системы кодирования товаров")
        print(f"2. Нужно проверить другие поля в OpenCart")
        print(f"3. Возможно, коды хранятся в атрибутах товаров")
    else:
        print(f"\n✅ Хорошее покрытие! Можно запускать синхронизацию.")
    
    return True

if __name__ == "__main__":
    auto_mapping()
