import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # DeepSeek API
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    # Model settings
    MODEL = "deepseek-chat"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.3
    
    # Nutrition calculation
    DEFAULT_CALORIES_PER_100G = 150
    MIN_CONFIDENCE_FOR_API = 0.7  # Gọi DeepSeek khi độ tin cậy < 70%
    ENABLE_DEEPSEEK = bool(DEEPSEEK_API_KEY)
    
    # API timeout
    REQUEST_TIMEOUT = 30
    
    @classmethod
    def is_deepseek_available(cls):
        return cls.ENABLE_DEEPSEEK and cls.DEEPSEEK_API_KEY
