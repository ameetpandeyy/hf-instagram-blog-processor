"""Job Processor - Orchestrates Instagram-to-blog pipeline"""
import logging
import httpx
import hashlib
import hmac
from typing import Dict, Any
from app.config import get_settings
from services.instagram_scraper import InstagramScraper
from services.gemini_generator import GeminiGenerator
from services.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize services (singleton pattern)
instagram_scraper = InstagramScraper()
gemini_generator = GeminiGenerator(
    api_key=settings.gemini_api_key,
    model_name=settings.gemini_model
)
supabase_client = SupabaseClient(
    url=settings.supabase_url,
    service_key=settings.supabase_service_key
)

async def send_callback(job_id: str, status: str, post_data: Dict[str, Any] = None, error: str = None):
    """Send callback to Next.js app"""
    try:
        payload = {
            "job_id": job_id,
            "status": status,
            "post_data": post_data,
            "error": error
        }
        
        # Generate HMAC signature
        message = f"{job_id}:{status}".encode()
        signature = hmac.new(
            settings.callback_secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "X-Callback-Signature": signature,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.callback_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"✅ Callback sent for job {job_id}")
            
    except Exception as e:
        logger.error(f"❌ Failed to send callback for {job_id}: {str(e)}")

async def process_instagram_job(job_id: str, instagram_url: str):
    """
    Process Instagram job - Full pipeline implementation
    
    Pipeline:
    1. Scrape Instagram post
    2. Generate blog with Gemini
    3. Create draft post in Supabase
    4. Send callback to Next.js
    
    Optional future enhancements:
    - Content classification (videos/books/products)
    - Social card generation
    - Affiliate link detection
    - YouTube video embedding
    """
    try:
        logger.info(f"🚀 Starting job {job_id} for {instagram_url}")
        
        # Update status: processing
        await supabase_client.update_job_status(job_id, "processing")
        
        # Step 1: Scrape Instagram
        logger.info(f"📸 Step 1/3: Scraping Instagram...")
        await supabase_client.update_job_status(
            job_id,
            "processing",
            progress={"step": "scraping", "message": "Extracting Instagram content..."}
        )
        
        reel_data = await instagram_scraper.scrape_post(instagram_url)
        
        # Step 2: Generate blog with Gemini
        logger.info(f"✍️  Step 2/3: Generating blog content...")
        await supabase_client.update_job_status(
            job_id,
            "processing",
            progress={"step": "generating", "message": "Creating blog article..."}
        )
        
        # Default to 'general' content type (classification can be added later)
        content_type = "general"
        
        blog_result = await gemini_generator.generate_blog(
            caption=reel_data.caption,
            content_type=content_type
        )
        
        # Step 3: Create draft post
        logger.info(f"💾 Step 3/3: Saving to database...")
        await supabase_client.update_job_status(
            job_id,
            "processing",
            progress={"step": "saving", "message": "Creating draft post..."}
        )
        
        post_id = await supabase_client.create_draft_post(
            instagram_url=instagram_url,
            title=blog_result["title"],
            content=blog_result["content"],
            content_type=content_type,
            youtube_links=reel_data.youtube_links,
            social_card_url=None,  # TODO: Add card generation
            affiliate_placeholders=None  # TODO: Add affiliate detection
        )
        
        # Update job: completed
        await supabase_client.update_job_status(job_id, "completed")
        
        # Send success callback
        post_data = {
            "post_id": post_id,
            "title": blog_result["title"],
            "word_count": blog_result["word_count"],
            "content_type": content_type,
            "youtube_links": reel_data.youtube_links
        }
        
        await send_callback(job_id, "completed", post_data=post_data)
        
        logger.info(f"✅ Job {job_id} completed successfully! Post ID: {post_id}")
        
        return {
            "status": "completed",
            "job_id": job_id,
            "post_id": post_id,
            "instagram_url": instagram_url
        }
        
    except Exception as e:
        error_message = f"Job failed: {str(e)}"
        logger.error(f"❌ Job {job_id} failed: {str(e)}", exc_info=True)
        
        # Update job: failed
        await supabase_client.update_job_status(
            job_id,
            "failed",
            error_message=error_message
        )
        
        # Send failure callback
        await send_callback(job_id, "failed", error=error_message)
        
        return {
            "status": "failed",
            "job_id": job_id,
            "error": error_message
        }
