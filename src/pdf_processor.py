import os
import re
import logging
from typing import List, Dict, Optional
import PyPDF2
import pandas as pd
from config import Config

logger = logging.getLogger(__name__)

class PDFProcessor:
    
    def __init__(self):
        self.download_dir = Config.DOWNLOAD_DIR
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            logger.info(f"Извлечен текст из PDF: {len(text)} символов")
            return text
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из PDF {pdf_path}: {e}")
            return ""
    
    def parse_metallprofil_data(self, text: str) -> List[Dict]:

        products = []
        
        try:
            # Разбиваем текст на строки
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Ищем строки с товарами и ценами
                # Примерный формат: "Название товара ... цена руб."
                price_pattern = r'(\d+[,.]?\d*)\s*руб'
                price_match = re.search(price_pattern, line)
                
                if price_match:
                    price = price_match.group(1).replace(',', '.')
                    
                    # Извлекаем название товара (все до цены)
                    product_name = re.sub(price_pattern, '', line).strip()
                    
                    # Извлекаем характеристики товара
                    thickness = self._extract_thickness(product_name)
                    coating_type = self._extract_coating_type(product_name)
                    
                    product = {
                        'name': product_name,
                        'price': float(price),
                        'thickness': thickness,
                        'coating_type': coating_type,
                        'source': 'metallprofil'
                    }
                    
                    products.append(product)
            
            logger.info(f"Извлечено {len(products)} товаров из PDF")
            return products
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге данных Металлпрофиль: {e}")
            return []
    
    def _extract_thickness(self, product_name: str) -> Optional[str]:

        # Ищем толщину в формате "0.5мм", "0,5 мм", "0.45"
        thickness_patterns = [
            r'(\d+[,.]?\d*)\s*мм',
            r'(\d+[,.]?\d*)\s*mm',
            r'толщина\s*(\d+[,.]?\d*)',
            r'(\d+[,.]?\d*)\s*(?=\s|$)'  # число в конце или перед пробелом
        ]
        
        for pattern in thickness_patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                return match.group(1).replace(',', '.')
        
        return None
    
    def _extract_coating_type(self, product_name: str) -> Optional[str]:

        coating_keywords = [
            'полиэстер', 'polyester', 'pe',
            'пурал', 'pural', 'pu',
            'пластизол', 'plastisol', 'pvc',
            'printech', 'принтек',
            'granite', 'гранит',
            'velur', 'велюр',
            'safari', 'сафари'
        ]
        
        product_lower = product_name.lower()
        
        for keyword in coating_keywords:
            if keyword in product_lower:
                return keyword.title()
        
        return None
    
    def filter_products_by_rules(self, products: List[Dict], rules: Dict) -> List[Dict]:

        filtered_products = []
        
        try:
            for product in products:
                # Проверяем правила фильтрации
                if self._matches_rules(product, rules):
                    filtered_products.append(product)
            
            logger.info(f"После фильтрации осталось {len(filtered_products)} товаров")
            return filtered_products
            
        except Exception as e:
            logger.error(f"Ошибка при фильтрации товаров: {e}")
            return products
    
    def _matches_rules(self, product: Dict, rules: Dict) -> bool:

        # Проверка толщины
        if 'thickness_range' in rules:
            thickness = product.get('thickness')
            if thickness:
                try:
                    thickness_float = float(thickness)
                    min_thickness = rules['thickness_range'].get('min', 0)
                    max_thickness = rules['thickness_range'].get('max', float('inf'))
                    
                    if not (min_thickness <= thickness_float <= max_thickness):
                        return False
                except ValueError:
                    pass
        
        # Проверка типа покрытия
        if 'coating_types' in rules:
            coating_type = product.get('coating_type')
            if coating_type and coating_type.lower() not in [ct.lower() for ct in rules['coating_types']]:
                return False
        
        # Проверка ключевых слов в названии
        if 'keywords' in rules:
            product_name = product.get('name', '').lower()
            keywords = rules['keywords']
            
            if 'include' in keywords:
                if not any(keyword.lower() in product_name for keyword in keywords['include']):
                    return False
            
            if 'exclude' in keywords:
                if any(keyword.lower() in product_name for keyword in keywords['exclude']):
                    return False
        
        return True
    
    def save_to_excel(self, products: List[Dict], filename: str) -> str:

        try:
            df = pd.DataFrame(products)
            
            # Создаем директорию если не существует
            os.makedirs(self.download_dir, exist_ok=True)
            
            file_path = os.path.join(self.download_dir, filename)
            df.to_excel(file_path, index=False)
            
            logger.info(f"Данные сохранены в Excel: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении в Excel: {e}")
            raise
    
    def save_to_csv(self, products: List[Dict], filename: str) -> str:

        try:
            df = pd.DataFrame(products)
            
            # Создаем директорию если не существует
            os.makedirs(self.download_dir, exist_ok=True)
            
            file_path = os.path.join(self.download_dir, filename)
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            logger.info(f"Данные сохранены в CSV: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении в CSV: {e}")
            raise
    
    def process_pdf_file(self, pdf_path: str, rules: Optional[Dict] = None) -> List[Dict]:

        try:
            logger.info(f"Начало обработки PDF файла: {pdf_path}")
            
            # Извлекаем текст
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                logger.error("Не удалось извлечь текст из PDF")
                return []
            
            # Парсим данные
            products = self.parse_metallprofil_data(text)
            if not products:
                logger.warning("Не найдено товаров в PDF")
                return []
            
            # Применяем фильтры если заданы
            if rules:
                products = self.filter_products_by_rules(products, rules)
            
            logger.info(f"Обработка PDF завершена. Получено {len(products)} товаров")
            return products
            
        except Exception as e:
            logger.error(f"Ошибка при обработке PDF файла: {e}")
            return []
