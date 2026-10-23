"""Job Processor - Orchestrates Instagram-to-blog pipeline with hero image generation"""
import logging
import httpx
import hashlib
import hmac
import re
import uuid
from typing import Dict, Any, List
from app.config import get_settings
from services.gemini_generator import GeminiGenerator
from services.supabase_client import SupabaseClient
from services.hero_image_generator import HeroImageGenerator

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize services
gemini_generator = GeminiGenerator(
    api_key=settings.gemini_api_key,
    model_name=settings.gemini_model
)
supabase_client = SupabaseClient(
    url=settings.supabase_url,
    service_key=settings.supabase_service_key
)
hero_image_generator = HeroImageGenerator()

def extract_youtube_links(text: str) -> List[str]:
    """Extract YouTube URLs from text"""
    if not text:
        return []
    
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
        r'https?://youtu\.be/[\w-]+',
    ]
    
    links = []
    for pattern in youtube_patterns:
        links.extend(re.findall(pattern, text))
    
    return list(set(links))

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
        
        # Use www.ameetpandey.com to avoid redirect
        callback_url = settings.callback_url.replace("https://ameetpandey.com", "https://www.ameetpandey.com")
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
            response = await client.post(
                callback_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"✅ Callback sent for job {job_id}")
            
    except Exception as e:
        logger.error(f"❌ Failed to send callback for {job_id}: {str(e)}")

async def process_instagram_job(job_id: str, instagram_url: str):
    """
    Process Instagram job using CSV metadata (NO SCRAPING)
    
    Pipeline:
    1. Use metadata from job (from CSV)
    2. Generate blog with Gemini
    3. Generate hero image
    4. Upload hero image to Supabase Storage
    5. Create media record in database
    6. Create draft post in Supabase
    7. Send callback to Next.js
    """
    try:
        logger.info(f"🚀 Starting job {job_id} for {instagram_url}")
        
        # Update status: processing
        await supabase_client.update_job_status(job_id, "processing")
        
        # Step 1: Get job metadata (from CSV via bulk import)
        logger.info(f"📋 Step 1/5: Fetching job metadata...")
        await supabase_client.update_job_status(
            job_id,
            "processing",
            progress={"step": "preparing", "message": "Loading metadata..."}
        )
        
        # Fetch job with metadata
        job_data = await supabase_client.get_job(job_id)
        metadata = job_data.get("metadata", {}) if job_data else {}
        
        # Extract data from metadata (populated by CSV bulk import)
        title = metadata.get("title", "Instagram Post")
        description = metadata.get("description", "")
        category = metadata.get("category", "")
        mentioned_content = metadata.get("mentioned_content", "")
        reference_links = metadata.get("reference_links", "")
        
        # Build caption from CSV data
        caption = f"""
Title: {title}

Description: {description}

Category: {category}

Mentioned: {mentioned_content}

References: {reference_links}
"""
        
        logger.info(f"✅ Using CSV metadata for {instagram_url}")
        
        # Extract YouTube links from references
        youtube_links = extract_youtube_links(reference_links + " " + mentioned_content)
        
        # Step 2: Generate blog with Gemini
        logger.info(f"✍️  Step 2/5: Generating blog content...")
        await supabase_client.update_job_status(
            job_id,
            "processing",
            progress={"step": "generating", "message": "Creating blog article..."}
        )
        
        # Determine content type from CSV
        content_type_map = {
            "video": "videos",
            "book": "books",
            "product": "products",
            "habit": "habits"
        }
        content_type = "general"
        for key, value in content_type_map.items():
            if key in category.lower() or key in title.lower():
                content_type = value
                break
        
        blog_result = await gemini_generator.generate_blog(
            caption=caption.strip(),
            content_type=content_type
        )
        
        # Step 3: Generate hero image
        logger.info(f"🎨 Step 3/5: Generating hero image...")
        await supabase_client.update_job_status(
            job_id,
            "processing",
            progress={"step": "generating_image", "message": "Creating hero image..."}
        )
        
        hero_image_bytes = hero_image_generator.generate_hero_image(blog_result["title"])
        
        # Step 4: Upload hero image to Supabase Storage
        logger.info(f"☁️  Step 4/5: Uploading hero image...")
        await supabase_client.update_job_status(
            job_id,
            "processing",
            progress={"step": "uploading", "message": "Uploading hero image..."}
        )
        
        # Generate unique filename
        image_filename = f"hero-{uuid.uuid4()}.png"
        storage_path = f"auto-generated/{image_filename}"
        
        hero_media_id = await supabase_client.upload_and_create_media(
            image_bytes=hero_image_bytes,
            storage_path=storage_path,
            alt_text=f"Hero image for: {blog_result['title']}",
            file_type="image/png",
            file_size=len(hero_image_bytes)
        )
        
        # Step 5: Create draft post
        logger.info(f"💾 Step 5/5: Saving to database...")
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
            youtube_links=youtube_links,
            hero_media_id=hero_media_id,
            affiliate_placeholders=None
        )
        
        # Update job: completed
        await supabase_client.update_job_status(job_id, "completed")
        
        # Send success callback
        post_data = {
            "post_id": post_id,
            "title": blog_result["title"],
            "word_count": blog_result["word_count"],
            "content_type": content_type,
            "youtube_links": youtube_links,
            "hero_media_id": hero_media_id
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