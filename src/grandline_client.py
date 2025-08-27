import requests
import logging
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class GrandLineClient:
    
    def __init__(self):
        self.api_key = Config.GRANDLINE_API_KEY
        self.branch_id = Config.GRANDLINE_BRANCH_ID
        self.agreement_id = Config.GRANDLINE_AGREEMENT_ID
        self.base_url = Config.GRANDLINE_BASE_URL
        self.session = requests.Session()
        
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def get_prices(self) -> List[Dict]:
        try:
            url = f"{self.base_url}/prices/"
            params = {
                'api_key': self.api_key,
                'branch_id': self.branch_id,
                'agreement_id': self.agreement_id,
                'limit': 20000,
                'offset': 0
            }
            
            logger.info(f"Requesting prices from GrandLine API: {url}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content type: {response.headers.get('content-type', 'unknown')}")
            logger.info(f"Response text (first 500 chars): {response.text[:500]}")
            
            data = response.json()
            
            # Проверяем на ошибки API
            if isinstance(data, dict) and 'error_code' in data:
                error_msg = data.get('error_message', 'Unknown error')
                logger.error(f"GrandLine API error {data.get('error_code')}: {error_msg}")
                logger.error(f"Sent parameters: {params}")
                return []
            
            logger.info(f"Received {len(data)} product positions")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error requesting GrandLine API: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def get_nomenclatures(self, nomenclature_ids: List[str]) -> Dict[str, str]:
        try:
            url = f"{self.base_url}/nomenclatures/"
            all_mappings = {}
            
            # Ограничиваем запрос только первой страницей чтобы избежать 429 ошибки
            limit = 20000
            offset = 0
            
            params = {
                'api_key': self.api_key,
                'limit': limit,
                'offset': offset
            }
            
            logger.info(f"Requesting nomenclatures with limit={limit}")
            
            # Retry логика для 502 и 429 ошибок
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code in [502, 429] and attempt < max_retries - 1:
                        wait_time = 10 if e.response.status_code == 429 else 5
                        logger.warning(f"{e.response.status_code} error, retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                        import time
                        time.sleep(wait_time)
                        continue
                    raise
            
            data = response.json()
            items = data.get('items', [])
            
            logger.info(f"Received {len(items)} nomenclature items from API")
            
            # Обрабатываем только нужные nomenclature_ids
            for item in items:
                nomenclature_id = item.get('id_1c')
                code_1c = item.get('code_1c')
                if nomenclature_id and code_1c and nomenclature_id in nomenclature_ids:
                    all_mappings[nomenclature_id] = code_1c
            
            logger.info(f"Received {len(all_mappings)} nomenclature_id -> code_1c mappings")
            return all_mappings
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error requesting nomenclature: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def process_prices_for_update(self) -> List[Dict]:
        try:
            prices_data = self.get_prices()
            
            if not prices_data:
                logger.warning("No price data received")
                return []
            
            logger.info(f"Prices data type: {type(prices_data)}")
            logger.info(f"Prices data content: {prices_data}")
            
            # Проверяем, что данные - это список
            if not isinstance(prices_data, list):
                logger.error(f"Expected list, got {type(prices_data)}: {prices_data}")
                return []
            
            # Проверяем первый элемент
            if prices_data and not isinstance(prices_data[0], dict):
                logger.error(f"Expected dict items, got {type(prices_data[0])}: {prices_data[0]}")
                return []
            
            nomenclature_ids = [item.get('nomenclature_id') for item in prices_data if isinstance(item, dict) and item.get('nomenclature_id')]
            
            if not nomenclature_ids:
                logger.warning("No nomenclature_id found in price data")
                return []
            
            nomenclature_mapping = self.get_nomenclatures(nomenclature_ids)
            
            update_list = []
            
            for item in prices_data:
                nomenclature_id = item.get('nomenclature_id')
                price = item.get('price')
                discount = item.get('discount')
                discount_price = item.get('discountPrice')
                
                if not nomenclature_id or not price:
                    continue
                
                code_1c = nomenclature_mapping.get(nomenclature_id)
                if not code_1c:
                    logger.warning(f"No code_1c found for nomenclature_id: {nomenclature_id}")
                    continue
                
                update_item = {
                    'code_1c': code_1c,
                    'price': str(price)
                }
                
                if discount:
                    update_item['discount'] = str(discount)
                if discount_price:
                    update_item['discountPrice'] = str(discount_price)
                
                update_list.append(update_item)
            
            logger.info(f"Prepared {len(update_list)} positions for price update")
            return update_list
            
        except Exception as e:
            logger.error(f"Error processing prices for update: {e}")
            raise
    
    def test_connection(self) -> bool:
        try:
            url = f"{self.base_url}/prices/"
            params = {
                'api_key': self.api_key,
                'branch_id': self.branch_id,
                'agreement_id': self.agreement_id
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            logger.info("GrandLine API connection successful")
            return True
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"GrandLine API HTTP error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"GrandLine API connection error: {e}")
            return False
