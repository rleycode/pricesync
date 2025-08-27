import logging
import mysql.connector
import psycopg2
import sqlite3
from typing import List, Dict, Optional, Union
from config import Config

logger = logging.getLogger(__name__)

class DatabaseUpdater:
    
    def __init__(self):
        self.db_type = Config.DATABASE_TYPE
        self.db_host = Config.DATABASE_HOST
        self.db_port = Config.DATABASE_PORT
        self.db_name = Config.DATABASE_NAME
        self.db_user = Config.DATABASE_USER
        self.db_password = Config.DATABASE_PASSWORD
        self.products_table = Config.DATABASE_PRODUCTS_TABLE
        self.price_field = Config.DATABASE_PRICE_FIELD
        self.code_field = Config.DATABASE_CODE_FIELD
        
        self.connection = None
    
    def connect(self) -> bool:
        try:
            if self.db_type.lower() == 'mysql':
                self.connection = mysql.connector.connect(
                    host=self.db_host,
                    port=self.db_port,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    charset='utf8mb4',
                    autocommit=False
                )
                
            elif self.db_type.lower() == 'postgresql':
                self.connection = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password
                )
                self.connection.autocommit = False
                
            elif self.db_type.lower() == 'sqlite':
                self.connection = sqlite3.connect(self.db_name)
                self.connection.execute("PRAGMA foreign_keys = ON")
                
            else:
                logger.error(f"Unsupported database type: {self.db_type}")
                return False
            
            logger.info(f"Successfully connected to database {self.db_type}")
            return True
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
    
    def update_single_price(self, code_1c: str, price: Union[str, float], 
                           discount: Optional[Union[str, float]] = None,
                           discount_price: Optional[Union[str, float]] = None) -> bool:
        if not self.connection:
            logger.error("No database connection")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            update_fields = [f"{self.price_field} = %s"]
            values = [float(price)]
            
            # Убираем поля discount и discount_price - их нет в oc_product
            
            # Добавляем условие WHERE
            values.append(code_1c)
            
            # Формируем SQL запрос
            sql = f"""
                UPDATE {self.products_table} 
                SET {', '.join(update_fields)}
                WHERE {self.code_field} = %s
            """
            
            # Адаптируем для SQLite (использует ? вместо %s)
            if self.db_type.lower() == 'sqlite':
                sql = sql.replace('%s', '?')
            
            logger.debug(f"SQL: {sql}")
            logger.debug(f"Values: {values}")
            
            cursor.execute(sql, values)
            
            # Проверяем, был ли обновлен товар
            if cursor.rowcount == 0:
                logger.warning(f"Товар с кодом {code_1c} не найден в БД")
                return False
            
            self.connection.commit()
            logger.info(f"Цена успешно обновлена для {code_1c}: {price}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении цены для {code_1c}: {e}")
            if self.connection:
                self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    def update_prices_batch(self, price_updates: List[Dict]) -> Dict[str, int]:
        """
        Массовое обновление цен в БД
        
        Args:
            price_updates: Список обновлений в формате [{"code_1c": "...", "price": "..."}]
            
        Returns:
            Dict[str, int]: Статистика обновлений {"success": count, "failed": count}
        """
        stats = {"success": 0, "failed": 0}
        
        if not self.connection:
            logger.error("Нет подключения к БД")
            stats["failed"] = len(price_updates)
            return stats
        
        logger.info(f"Начало массового обновления {len(price_updates)} цен в БД")
        
        try:
            cursor = self.connection.cursor()
            
            for update in price_updates:
                try:
                    code_1c = update.get('code_1c')
                    price = update.get('price')
                    discount = update.get('discount')
                    discount_price = update.get('discountPrice')
                    
                    if not code_1c or not price:
                        logger.warning("Пропущено обновление: отсутствует code_1c или price")
                        stats["failed"] += 1
                        continue
                    
                    # Формируем запрос для каждого товара
                    update_fields = [f"{self.price_field} = %s"]
                    values = [float(price)]
                    
                    # Убираем поля discount и discount_price - их нет в oc_product
                    
                    values.append(code_1c)
                    
                    sql = f"""
                        UPDATE {self.products_table} 
                        SET {', '.join(update_fields)}
                        WHERE {self.code_field} = %s
                    """
                    
                    if self.db_type.lower() == 'sqlite':
                        sql = sql.replace('%s', '?')
                    
                    cursor.execute(sql, values)
                    
                    if cursor.rowcount > 0:
                        stats["success"] += 1
                    else:
                        logger.warning(f"Товар {code_1c} не найден в БД")
                        stats["failed"] += 1
                
                except Exception as e:
                    logger.error(f"Ошибка при обновлении {code_1c}: {e}")
                    stats["failed"] += 1
                    continue
            
            # Коммитим все изменения
            self.connection.commit()
            
            logger.info(f"Массовое обновление завершено. Успешно: {stats['success']}, ошибок: {stats['failed']}")
            return stats
            
        except Exception as e:
            logger.error(f"Критическая ошибка при массовом обновлении: {e}")
            if self.connection:
                self.connection.rollback()
            stats["failed"] = len(price_updates)
            return stats
        finally:
            if cursor:
                cursor.close()
    
    def get_product_info(self, code_1c: str) -> Optional[Dict]:
        """
        Получение информации о товаре по code_1c
        
        Args:
            code_1c: Код товара в 1C
            
        Returns:
            Optional[Dict]: Информация о товаре или None
        """
        if not self.connection:
            logger.error("Нет подключения к БД")
            return None
        
        try:
            cursor = self.connection.cursor()
            
            sql = f"""
                SELECT {self.code_field}, {self.price_field}
                FROM {self.products_table}
                WHERE {self.code_field} = %s
            """
            
            if self.db_type.lower() == 'sqlite':
                sql = sql.replace('%s', '?')
            
            cursor.execute(sql, (code_1c,))
            result = cursor.fetchone()
            
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации о товаре {code_1c}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def test_connection(self) -> bool:
        """
        Проверка соединения с БД
        
        Returns:
            bool: True если соединение успешно
        """
        try:
            if not self.connect():
                return False
            
            cursor = self.connection.cursor()
            
            # Простой тестовый запрос
            if self.db_type.lower() == 'mysql':
                cursor.execute("SELECT 1")
            elif self.db_type.lower() == 'postgresql':
                cursor.execute("SELECT 1")
            elif self.db_type.lower() == 'sqlite':
                cursor.execute("SELECT 1")
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                logger.info("Тест соединения с БД успешен")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка тестирования соединения с БД: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_products_count(self) -> int:
        """
        Получение количества товаров в БД
        
        Returns:
            int: Количество товаров
        """
        if not self.connection:
            logger.error("Нет подключения к БД")
            return 0
        
        try:
            cursor = self.connection.cursor()
            
            sql = f"SELECT COUNT(*) FROM {self.products_table}"
            cursor.execute(sql)
            result = cursor.fetchone()
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Ошибка при подсчете товаров: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
    
    def validate_price_updates(self, price_updates: List[Dict]) -> List[Dict]:
        """
        Валидация данных для обновления цен
        
        Args:
            price_updates: Список обновлений
            
        Returns:
            List[Dict]: Валидные обновления
        """
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
                update['price'] = price_float
                
            except ValueError:
                logger.warning(f"Пропущено обновление для {code_1c}: некорректный формат цены")
                continue
            
            valid_updates.append(update)
        
        logger.info(f"Валидация завершена: {len(valid_updates)} из {len(price_updates)} обновлений прошли проверку")
        return valid_updates
