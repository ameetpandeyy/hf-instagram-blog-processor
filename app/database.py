import logging
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)

supabase_client: Client | None = None

def get_supabase() -> Client:
    global supabase_client
    if supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            logger.warning("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not configured. Running in mock/development mode.")
        try:
            supabase_client = create_client(
                supabase_url=settings.SUPABASE_URL or "https://placeholder-project.supabase.co",
                supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY or "placeholder-key"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    return supabase_client
