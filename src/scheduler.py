"""
Модуль планировщика задач для автоматического обновления цен
"""
import schedule
import time
import logging
from datetime import datetime
from typing import Callable, Optional
from config import Config
from src.logger import log_execution_time

logger = logging.getLogger('pricesync')

class PriceSyncScheduler:
    
    def __init__(self):
        self.sync_time = Config.SYNC_SCHEDULE_TIME
        self.is_running = False
        self.sync_callback: Optional[Callable] = None
    
    def set_sync_callback(self, callback: Callable):

        self.sync_callback = callback
        logger.info(f"Установлена функция синхронизации: {callback.__name__}")
    
    @log_execution_time
    def run_sync(self):
        if not self.sync_callback:
            logger.error("Не установлена функция синхронизации")
            return
        
        try:
            logger.info("Запуск автоматической синхронизации цен")
            self.sync_callback()
            logger.info("Автоматическая синхронизация завершена успешно")
        except Exception as e:
            logger.error(f"Ошибка при автоматической синхронизации: {e}")
    
    def schedule_daily_sync(self):
        schedule.clear()  # Очищаем предыдущие задачи
        
        schedule.every().day.at(self.sync_time).do(self.run_sync)
        logger.info(f"Запланирована ежедневная синхронизация в {self.sync_time}")
    
    def schedule_custom(self, interval_type: str, interval: int, time_str: Optional[str] = None):

        schedule.clear()
        
        if interval_type == 'minutes':
            schedule.every(interval).minutes.do(self.run_sync)
            logger.info(f"Запланирована синхронизация каждые {interval} минут")
        elif interval_type == 'hours':
            schedule.every(interval).hours.do(self.run_sync)
            logger.info(f"Запланирована синхронизация каждые {interval} часов")
        elif interval_type == 'days':
            if time_str:
                schedule.every(interval).days.at(time_str).do(self.run_sync)
                logger.info(f"Запланирована синхронизация каждые {interval} дней в {time_str}")
            else:
                schedule.every(interval).days.do(self.run_sync)
                logger.info(f"Запланирована синхронизация каждые {interval} дней")
    
    def start(self):
        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return
        
        if not self.sync_callback:
            logger.error("Не установлена функция синхронизации. Планировщик не может быть запущен")
            return
        
        self.is_running = True
        logger.info("Планировщик запущен")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки планировщика")
        finally:
            self.stop()
    
    def stop(self):
        self.is_running = False
        schedule.clear()
        logger.info("Планировщик остановлен")
    
    def get_next_run_time(self) -> Optional[datetime]:

        jobs = schedule.get_jobs()
        if not jobs:
            return None
        
        next_run = min(job.next_run for job in jobs)
        return next_run
    
    def run_once(self):
        logger.info("Запуск разовой синхронизации")
        self.run_sync()
    
    def get_status(self) -> dict:

        jobs = schedule.get_jobs()
        next_run = self.get_next_run_time()
        
        return {
            'is_running': self.is_running,
            'jobs_count': len(jobs),
            'next_run': next_run.isoformat() if next_run else None,
            'sync_callback_set': self.sync_callback is not None
        }
