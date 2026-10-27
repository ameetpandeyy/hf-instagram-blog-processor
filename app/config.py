import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase Configuration (Server-side service key only)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Firebase Admin Configuration
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "teamo-ea8f2")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")

    # Gemini AI Configuration (Cost-optimized: gemini-2.0-flash / gemini-1.5-flash)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_CHAT_MODEL: str = os.getenv("DEFAULT_CHAT_MODEL", "gemini-2.0-flash")
    MEMORY_EXTRACTION_MODEL: str = os.getenv("MEMORY_EXTRACTION_MODEL", "gemini-2.0-flash")

    # Security & Admin
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "teamo_secret_admin_key_2026")
    ADMOB_SSV_KEY: str = os.getenv("ADMOB_SSV_KEY", "")

    # Server Port (Hugging Face default is 7860)
    PORT: int = int(os.getenv("PORT", "7860"))

settings = Settings()
