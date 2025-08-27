"""
Модуль для настройки логирования
"""
import os
import logging
import logging.handlers
from datetime import datetime
from config import Config

def setup_logging(log_level: str = 'INFO') -> logging.Logger:

    os.makedirs(Config.LOG_DIR, exist_ok=True)
    

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    

    logger = logging.getLogger('pricesync')
    logger.setLevel(getattr(logging, log_level.upper()))
    

    logger.handlers.clear()
    
    # Консольный вывод
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    

    log_file = os.path.join(Config.LOG_DIR, 'pricesync.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    

    error_log_file = os.path.join(Config.LOG_DIR, 'errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

def log_execution_time(func):

    def wrapper(*args, **kwargs):
        logger = logging.getLogger('pricesync')
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"{func.__name__} выполнена за {execution_time:.2f} сек")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func.__name__} завершилась с ошибкой за {execution_time:.2f} сек: {e}")
            raise
    
    return wrapper
