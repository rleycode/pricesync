import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GRANDLINE_API_KEY = os.getenv('GRANDLINE_API_KEY')
    GRANDLINE_BRANCH_ID = os.getenv('GRANDLINE_BRANCH_ID')
    GRANDLINE_AGREEMENT_ID = os.getenv('GRANDLINE_AGREEMENT_ID')
    GRANDLINE_BASE_URL = os.getenv('GRANDLINE_BASE_URL', 'https://api.grandline.ru')
    
    METALLPROFIL_LOGIN = os.getenv('METALLPROFIL_LOGIN')
    METALLPROFIL_PASSWORD = os.getenv('METALLPROFIL_PASSWORD')
    METALLPROFIL_URL = os.getenv('METALLPROFIL_URL', 'https://lk.metallprofil.ru')
    
    WEBSITE_API_URL = os.getenv('WEBSITE_API_URL')
    WEBSITE_API_KEY = os.getenv('WEBSITE_API_KEY')
    
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'mysql')
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    DATABASE_PORT = int(os.getenv('DATABASE_PORT', '3306'))
    DATABASE_NAME = os.getenv('DATABASE_NAME')
    DATABASE_USER = os.getenv('DATABASE_USER')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
    
    DATABASE_PRODUCTS_TABLE = os.getenv('DATABASE_PRODUCTS_TABLE', 'products')
    DATABASE_CODE_FIELD = os.getenv('DATABASE_CODE_FIELD', 'code_1c')
    DATABASE_PRICE_FIELD = os.getenv('DATABASE_PRICE_FIELD', 'price')
    
    DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', './downloads')
    LOG_DIR = os.getenv('LOG_DIR', './logs')
    
    BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'True').lower() == 'true'
    BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', '30'))
    
    SYNC_SCHEDULE_TIME = os.getenv('SYNC_SCHEDULE_TIME', '09:00')
    
    @classmethod
    def validate_config(cls):
        required_fields = [
            'GRANDLINE_API_KEY',
            'GRANDLINE_BRANCH_ID', 
            'GRANDLINE_AGREEMENT_ID',
            'METALLPROFIL_LOGIN',
            'METALLPROFIL_PASSWORD',
            'WEBSITE_API_URL'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required settings: {', '.join(missing_fields)}")
        
        return True
