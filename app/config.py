from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash"
    
    # Supabase
    supabase_url: str
    supabase_service_key: str
    
    # Webhook Security
    webhook_secret: str
    callback_url: str
    callback_secret: str
    
    # Application
    log_level: str = "INFO"
    max_workers: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

