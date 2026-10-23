"""Supabase Client - Database operations"""
import logging
from typing import Dict, Optional, Any
from supabase import create_client, Client
from datetime import datetime
import re

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
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL-safe slug from title"""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:100]  # Limit length
    
    def _extract_meta_description(self, content: str) -> str:
        """Extract first 160 chars from content for meta description"""
        # Remove markdown headings
        lines = [line for line in content.split('\n') if not line.startswith('#')]
        text = ' '.join(lines).strip()
        # Take first 160 chars
        return text[:160] + ('...' if len(text) > 160 else '')
    
    def _calculate_read_time(self, content: str) -> int:
        """Calculate reading time in minutes (200 words/min)"""
        word_count = len(content.split())
        return max(1, round(word_count / 200))
    
    async def upload_and_create_media(
        self,
        image_bytes: bytes,
        storage_path: str,
        alt_text: str,
        file_type: str = "image/png",
        file_size: int = 0
    ) -> str:
        """
        Upload image to Supabase Storage and create media record
        
        Returns:
            Media UUID
        """
        try:
            # Upload to storage (bucket: media)
            self.client.storage.from_("media").upload(
                storage_path,
                image_bytes,
                file_options={"content-type": file_type}
            )
            
            logger.info(f"✅ Uploaded image to storage: {storage_path}")
            
            # Create media record (only columns that exist in schema)
            media_data = {
                "storage_path": storage_path,
                "alt_text": alt_text,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("media").insert(media_data).execute()
            media_id = result.data[0]["id"]
            
            logger.info(f"✅ Created media record: {media_id}")
            return media_id
            
        except Exception as e:
            logger.error(f"❌ Failed to upload and create media: {str(e)}")
            raise
    
    async def create_draft_post(
        self,
        instagram_url: str,
        title: str,
        content: str,
        content_type: str,
        youtube_links: list,
        hero_media_id: Optional[str] = None,
        affiliate_placeholders: Optional[list] = None
    ) -> str:
        """
        Create draft post in posts table matching the actual schema
        
        Returns:
            Post UUID
        """
        try:
            slug = self._generate_slug(title)
            meta_description = self._extract_meta_description(content)
            read_minutes = self._calculate_read_time(content)
            
            # Add Instagram URL and YouTube links as metadata in the content
            footer = f"\n\n---\n\n**Source**: [Instagram Post]({instagram_url})\n\n"
            if youtube_links:
                footer += "**Referenced Videos**:\n"
                for link in youtube_links:
                    footer += f"- {link}\n"
            
            post_data = {
                "slug": slug,
                "title": title,
                "body_md": content + footer,
                "meta_description": meta_description,
                "status": "draft",
                "read_minutes": read_minutes,
                "affiliate": bool(affiliate_placeholders),
                "hero_media_id": hero_media_id,
                "ig_caption": f"From Instagram: {instagram_url}",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("posts").insert(post_data).execute()
            
            post_id = result.data[0]["id"]
            logger.info(f"✅ Created draft post: {post_id} ({slug})")
            
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
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        try:
            result = self.client.table("processing_jobs").select("*").eq("id", job_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"❌ Failed to fetch job {job_id}: {str(e)}")
            return None