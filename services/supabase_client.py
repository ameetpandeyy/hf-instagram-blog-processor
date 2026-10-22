"""Supabase Client - Database operations"""
import logging
from typing import Dict, Optional, Any
from supabase import create_client, Client
from datetime import datetime

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self, url: str, service_key: str):
        self.client: Client = create_client(url, service_key)
        logger.info("Supabase client initialized")
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
        progress: Optional[Dict[str, Any]] = None
    ):
        """
        Update job status in processing_jobs table
        
        Args:
            job_id: Job UUID
            status: One of: pending, processing, completed, failed
            error_message: Error details if failed
            progress: Progress data (optional)
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            if progress:
                update_data["progress"] = progress
            
            result = self.client.table("processing_jobs").update(update_data).eq("id", job_id).execute()
            
            logger.info(f"✅ Updated job {job_id} status: {status}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to update job {job_id}: {str(e)}")
            raise
    
    async def create_draft_post(
        self,
        instagram_url: str,
        title: str,
        content: str,
        content_type: str,
        youtube_links: list,
        social_card_url: Optional[str] = None,
        affiliate_placeholders: Optional[list] = None
    ) -> str:
        """
        Create draft post in posts table
        
        Returns:
            Post UUID
        """
        try:
            post_data = {
                "title": title,
                "content": content,
                "instagram_url": instagram_url,
                "content_type": content_type,
                "youtube_links": youtube_links,
                "status": "draft",
                "needs_finalization": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if social_card_url:
                post_data["social_card_url"] = social_card_url
            
            if affiliate_placeholders:
                post_data["affiliate_links"] = affiliate_placeholders
            
            result = self.client.table("posts").insert(post_data).execute()
            
            post_id = result.data[0]["id"]
            logger.info(f"✅ Created draft post: {post_id}")
            
            return post_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create draft post: {str(e)}")
            raise
    
    async def upload_social_card(
        self,
        image_bytes: bytes,
        filename: str,
        bucket: str = "social-cards"
    ) -> str:
        """
        Upload social card image to Supabase Storage
        
        Returns:
            Public URL of uploaded image
        """
        try:
            # Upload to storage
            result = self.client.storage.from_(bucket).upload(
                filename,
                image_bytes,
                file_options={"content-type": "image/png"}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(bucket).get_public_url(filename)
            
            logger.info(f"✅ Uploaded social card: {filename}")
            return public_url
            
        except Exception as e:
            logger.error(f"❌ Failed to upload social card: {str(e)}")
            raise
    
    async def get_pending_job(self) -> Optional[Dict[str, Any]]:
        """Get next pending job from queue"""
        try:
            result = self.client.table("processing_jobs").select("*").eq("status", "pending").order("created_at").limit(1).execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch pending job: {str(e)}")
            raise
