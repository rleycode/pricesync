#!/usr/bin/env python3
"""
Примеры использования системы PriceSync
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import PriceSyncManager

def example_test_connections():
    """Пример проверки соединений"""
    print("=== Проверка соединений ===")
    
    manager = PriceSyncManager()
    results = manager.test_connections()
    
    for source, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{source.upper()}: {status_icon}")

def example_grandline_sync():
    """Пример синхронизации с GrandLine"""
    print("=== Синхронизация GrandLine ===")
    
    manager = PriceSyncManager()
    success = manager.sync_grandline()
    
    if success:
        print("✅ GrandLine синхронизация успешна")
    else:
        print("❌ Ошибка синхронизации GrandLine")

def example_metallprofil_sync():
    """Пример синхронизации с Металлпрофиль"""
    print("=== Синхронизация Металлпрофиль ===")
    
    # Настройка правил обработки
    processing_rules = {
        'thickness_range': {'min': 0.4, 'max': 1.0},
        'coating_types': ['полиэстер', 'пурал', 'printech'],
        'keywords': {
            'include': ['профнастил', 'металлочерепица', 'сайдинг'],
            'exclude': ['брак', 'б/у', 'остаток']
        }
    }
    
    manager = PriceSyncManager()
    success = manager.sync_metallprofil(processing_rules)
    
    if success:
        print("✅ Металлпрофиль синхронизация успешна")
    else:
        print("❌ Ошибка синхронизации Металлпрофиль")

def example_full_sync():
    """Пример полной синхронизации"""
    print("=== Полная синхронизация ===")
    
    manager = PriceSyncManager()
    results = manager.sync_all_sources()
    
    print(f"GrandLine: {'✅' if results['grandline'] else '❌'}")
    print(f"Металлпрофиль: {'✅' if results['metallprofil'] else '❌'}")
    print(f"Время: {results['timestamp']}")

def example_scheduler_usage():
    """Пример использования планировщика"""
    print("=== Планировщик ===")
    
    manager = PriceSyncManager()
    
    # Получение статуса
    status = manager.scheduler.get_status()
    print(f"Статус планировщика: {status}")
    
    # Настройка пользовательского расписания
    # Каждые 2 часа
    manager.scheduler.schedule_custom('hours', 2)
    
    # Ежедневно в 10:30
    manager.scheduler.schedule_custom('days', 1, '10:30')
    
    print("Планировщик настроен")

if __name__ == "__main__":
    print("🚀 Примеры использования PriceSync\n")
    
    try:
        # Раскомментируйте нужные примеры
        
        # example_test_connections()
        # example_grandline_sync()
        # example_metallprofil_sync()
        # example_full_sync()
        # example_scheduler_usage()
        
        print("\n✨ Для запуска примеров раскомментируйте нужные функции")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("Убедитесь, что настроен .env файл и установлены зависимости")
