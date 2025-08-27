import sys
import argparse
from datetime import datetime
from config import Config
from src.logger import setup_logging, log_execution_time
from src.grandline_client import GrandLineClient
from src.metallprofil_scraper import MetallprofilScraper
from src.pdf_processor import PDFProcessor
from src.website_updater import WebsiteUpdater
from src.database_updater import DatabaseUpdater
from src.scheduler import PriceSyncScheduler

logger = setup_logging()

class PriceSyncManager:
    
    def __init__(self):
        try:
            Config.validate_config()
            logger.info("Configuration loaded successfully")
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        
        self.grandline_client = GrandLineClient()
        self.metallprofil_scraper = MetallprofilScraper()
        self.pdf_processor = PDFProcessor()
        self.website_updater = WebsiteUpdater()
        self.database_updater = DatabaseUpdater()
        self.scheduler = PriceSyncScheduler()
        
        self.scheduler.set_sync_callback(self.sync_all_sources)
    
    @log_execution_time
    def sync_grandline(self) -> bool:
        try:
            logger.info("Starting GrandLine synchronization")
            
            price_updates = self.grandline_client.process_prices_for_update()
            
            if not price_updates:
                logger.warning("No data to update from GrandLine")
                return False
            
            valid_updates = self.database_updater.validate_price_updates(price_updates)
            
            if not valid_updates:
                logger.error("All GrandLine data failed validation")
                return False
            
            if not self.database_updater.connect():
                logger.error("Failed to connect to database")
                return False
            
            try:
                stats = self.database_updater.update_prices_batch(valid_updates)
            finally:
                self.database_updater.disconnect()
            
            logger.info(f"GrandLine sync completed. Success: {stats['success']}, failed: {stats['failed']}")
            return stats['success'] > 0
            
        except Exception as e:
            logger.error(f"Error syncing with GrandLine: {e}")
            return False
    
    @log_execution_time
    def sync_metallprofil(self, processing_rules: dict = None) -> bool:
        try:
            logger.info("Starting Metallprofil synchronization")
            
            pdf_path = self.metallprofil_scraper.scrape_pricelist()
            
            if not pdf_path:
                logger.error("Failed to get pricelist from Metallprofil")
                return False
            
            products = self.pdf_processor.process_pdf_file(pdf_path, processing_rules)
            
            if not products:
                logger.warning("No products found in Metallprofil pricelist")
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = f"metallprofil_prices_{timestamp}.xlsx"
            self.pdf_processor.save_to_excel(products, excel_file)
            
            logger.info(f"Metallprofil sync completed. Processed {len(products)} products")
            logger.info(f"Data saved to file: {excel_file}")
            
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing with Metallprofil: {e}")
            return False
    
    @log_execution_time
    def sync_all_sources(self) -> dict:
        results = {
            'grandline': False,
            'metallprofil': False,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("Starting full synchronization of all sources")
        
        try:
            results['grandline'] = self.sync_grandline()
        except Exception as e:
            logger.error(f"Critical error syncing GrandLine: {e}")
        
        try:
            processing_rules = {
                'thickness_range': {'min': 0.4, 'max': 1.0},
                'coating_types': ['полиэстер', 'пурал'],
                'keywords': {
                    'include': ['профнастил', 'металлочерепица'],
                    'exclude': ['брак', 'б/у']
                }
            }
            results['metallprofil'] = self.sync_metallprofil(processing_rules)
        except Exception as e:
            logger.error(f"Critical error syncing Metallprofil: {e}")
        
        success_count = sum(1 for result in results.values() if result is True)
        logger.info(f"Full synchronization completed. Successful sources: {success_count}/2")
        
        return results
    
    def test_connections(self) -> dict:
        results = {}
        
        logger.info("Testing connections to external sources")
        
        try:
            results['grandline'] = self.grandline_client.test_connection()
        except Exception as e:
            logger.error(f"Error testing GrandLine: {e}")
            results['grandline'] = False
        
        try:
            results['metallprofil'] = self.metallprofil_scraper.test_connection()
        except Exception as e:
            logger.error(f"Error testing Metallprofil: {e}")
            results['metallprofil'] = False
        
        try:
            results['database'] = self.database_updater.test_connection()
        except Exception as e:
            logger.error(f"Error testing database: {e}")
            results['database'] = False
        
        return results
    
    def start_scheduler(self):
        logger.info("Starting automatic synchronization scheduler")
        self.scheduler.schedule_daily_sync()
        self.scheduler.start()
    
    def run_once(self):
        return self.sync_all_sources()

def main():
    parser = argparse.ArgumentParser(description='Price synchronization system')
    parser.add_argument('--mode', choices=['once', 'schedule', 'test'], 
                       default='once', help='Operation mode')
    parser.add_argument('--source', choices=['grandline', 'metallprofil', 'all'], 
                       default='all', help='Source for synchronization')
    
    args = parser.parse_args()
    
    manager = PriceSyncManager()
    
    if args.mode == 'test':
        logger.info("Connection testing mode")
        results = manager.test_connections()
        
        print("\n=== Connection Test Results ===")
        for source, status in results.items():
            status_text = "✓ OK" if status else "✗ FAIL"
            print(f"{source.upper()}: {status_text}")
        
        return
    
    elif args.mode == 'once':
        logger.info("Single synchronization mode")
        
        if args.source == 'grandline':
            success = manager.sync_grandline()
        elif args.source == 'metallprofil':
            success = manager.sync_metallprofil()
        else:
            results = manager.run_once()
            success = any(results.values())
        
        if success:
            logger.info("Synchronization completed successfully")
        else:
            logger.error("Synchronization completed with errors")
            sys.exit(1)
    
    elif args.mode == 'schedule':
        logger.info("Scheduler mode")
        try:
            manager.start_scheduler()
        except KeyboardInterrupt:
            logger.info("Stop signal received")
        except Exception as e:
            logger.error(f"Critical scheduler error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
