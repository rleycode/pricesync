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
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def get_prices(self) -> List[Dict]:
        try:
            url = f"{self.base_url}/prices/"
            params = {
                'api_key': self.api_key,
                'branch_id': self.branch_id,
                'agreement_id': self.agreement_id
            }
            
            logger.info(f"Requesting prices from GrandLine API: {url}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
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
            
            batch_size = 100
            all_mappings = {}
            
            for i in range(0, len(nomenclature_ids), batch_size):
                batch = nomenclature_ids[i:i + batch_size]
                
                params = {
                    'api_key': self.api_key,
                    'nomenclature_ids': ','.join(batch)
                }
                
                logger.info(f"Requesting nomenclature for {len(batch)} positions")
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                for item in data:
                    nomenclature_id = item.get('nomenclature_id')
                    code_1c = item.get('code_1c')
                    if nomenclature_id and code_1c:
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
            
            nomenclature_ids = [item.get('nomenclature_id') for item in prices_data if item.get('nomenclature_id')]
            
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
            url = f"{self.base_url}/test"
            params = {'api_key': self.api_key}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            logger.info("GrandLine API connection successful")
            return True
            
        except Exception as e:
            logger.error(f"GrandLine API connection error: {e}")
            return False
