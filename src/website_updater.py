import requests
import logging
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class WebsiteUpdater:

    def __init__(self):
        self.api_url = Config.WEBSITE_API_URL
        self.api_key = Config.WEBSITE_API_KEY
        self.session = requests.Session()
        
        # Настройка заголовков
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def update_single_price(self, code_1c: str, price: str, discount: Optional[str] = None, 
                           discount_price: Optional[str] = None) -> bool:
        try:
            url = f"{self.api_url}/products/{code_1c}/price"
            
            data = {
                'code_1c': code_1c,
                'price': price
            }
            
            # Добавляем скидки если есть
            if discount:
                data['discount'] = discount
            if discount_price:
                data['discount_price'] = discount_price
            
            logger.debug(f"Обновление цены для {code_1c}: {price}")
            response = self.session.put(url, json=data)
            response.raise_for_status()
            
            logger.info(f"Цена успешно обновлена для {code_1c}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при обновлении цены для {code_1c}: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обновлении {code_1c}: {e}")
            return False
    
    def update_prices_batch(self, price_updates: List[Dict]) -> Dict[str, int]:

        stats = {"success": 0, "failed": 0}
        
        try:
            url = f"{self.api_url}/products/prices/batch"
            
            logger.info(f"Начало массового обновления {len(price_updates)} цен")
            
            # Отправляем батчами по 100 товаров
            batch_size = 100
            
            for i in range(0, len(price_updates), batch_size):
                batch = price_updates[i:i + batch_size]
                
                try:
                    response = self.session.put(url, json={'updates': batch})
                    response.raise_for_status()
                    
                    result = response.json()
                    batch_success = result.get('success_count', len(batch))
                    batch_failed = result.get('failed_count', 0)
                    
                    stats["success"] += batch_success
                    stats["failed"] += batch_failed
                    
                    logger.info(f"Батч {i//batch_size + 1}: успешно {batch_success}, ошибок {batch_failed}")
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Ошибка при обновлении батча {i//batch_size + 1}: {e}")
                    stats["failed"] += len(batch)
            
            logger.info(f"Массовое обновление завершено. Успешно: {stats['success']}, ошибок: {stats['failed']}")
            return stats
            
        except Exception as e:
            logger.error(f"Критическая ошибка при массовом обновлении: {e}")
            stats["failed"] = len(price_updates)
            return stats
    
    def update_prices_individually(self, price_updates: List[Dict]) -> Dict[str, int]:

        stats = {"success": 0, "failed": 0}
        
        logger.info(f"Начало индивидуального обновления {len(price_updates)} цен")
        
        for update in price_updates:
            code_1c = update.get('code_1c')
            price = update.get('price')
            discount = update.get('discount')
            discount_price = update.get('discountPrice')
            
            if not code_1c or not price:
                logger.warning(f"Пропущено обновление: отсутствует code_1c или price")
                stats["failed"] += 1
                continue
            
            if self.update_single_price(code_1c, price, discount, discount_price):
                stats["success"] += 1
            else:
                stats["failed"] += 1
        
        logger.info(f"Индивидуальное обновление завершено. Успешно: {stats['success']}, ошибок: {stats['failed']}")
        return stats
    
    def update_prices(self, price_updates: List[Dict], use_batch: bool = True) -> Dict[str, int]:

        if not price_updates:
            logger.warning("Нет данных для обновления цен")
            return {"success": 0, "failed": 0}
        
        if use_batch:
            return self.update_prices_batch(price_updates)
        else:
            return self.update_prices_individually(price_updates)
    
    def test_connection(self) -> bool:

        try:
            url = f"{self.api_url}/health"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            logger.info("Соединение с API сайта успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка соединения с API сайта: {e}")
            return False
    
    def get_product_info(self, code_1c: str) -> Optional[Dict]:

        try:
            url = f"{self.api_url}/products/{code_1c}"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении информации о товаре {code_1c}: {e}")
            return None
    
    def validate_price_updates(self, price_updates: List[Dict]) -> List[Dict]:

        valid_updates = []
        
        for update in price_updates:
            code_1c = update.get('code_1c')
            price = update.get('price')
            
            # Проверяем обязательные поля
            if not code_1c:
                logger.warning("Пропущено обновление: отсутствует code_1c")
                continue
            
            if not price:
                logger.warning(f"Пропущено обновление для {code_1c}: отсутствует price")
                continue
            
            # Проверяем формат цены
            try:
                price_float = float(str(price).replace(',', '.'))
                if price_float < 0:
                    logger.warning(f"Пропущено обновление для {code_1c}: отрицательная цена")
                    continue
                
                # Нормализуем цену
                update['price'] = str(price_float)
                
            except ValueError:
                logger.warning(f"Пропущено обновление для {code_1c}: некорректный формат цены")
                continue
            
            valid_updates.append(update)
        
        logger.info(f"Валидация завершена: {len(valid_updates)} из {len(price_updates)} обновлений прошли проверку")
        return valid_updates
