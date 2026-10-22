"""Instagram Scraper - Extract content from Instagram posts"""
import re
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
import instaloader

logger = logging.getLogger(__name__)

@dataclass
class InstagramReelData:
    caption: str
    media_url: str
    posted_date: str
    video_url: Optional[str]
    youtube_links: List[str]
    shortcode: str

class InstagramScraper:
    def __init__(self):
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True
        )
        logger.info("Instagram scraper initialized")
    
    def extract_youtube_links(self, text: str) -> List[str]:
        """Extract YouTube URLs from text"""
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
            r'https?://youtu\.be/[\w-]+',
        ]
        
        links = []
        for pattern in youtube_patterns:
            links.extend(re.findall(pattern, text))
        
        return list(set(links))  # Remove duplicates
    
    def extract_shortcode(self, url: str) -> str:
        """Extract Instagram shortcode from URL"""
        patterns = [
            r'instagram\.com/p/([\w-]+)',
            r'instagram\.com/reel/([\w-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Invalid Instagram URL: {url}")
    
    async def scrape_post(self, instagram_url: str) -> InstagramReelData:
        """
        Scrape Instagram post content
        
        Args:
            instagram_url: Full Instagram URL (e.g., https://www.instagram.com/p/ABC123/)
        
        Returns:
            InstagramReelData with extracted content
        
        Raises:
            ValueError: If URL is invalid or post cannot be scraped
        """
        try:
            shortcode = self.extract_shortcode(instagram_url)
            logger.info(f"Scraping Instagram post: {shortcode}")
            
            # Load post without authentication
            post = instaloader.Post.from_shortcode(
                self.loader.context,
                shortcode
            )
            
            # Extract data
            caption = post.caption or ""
            media_url = post.url
            posted_date = post.date_utc.isoformat()
            video_url = post.video_url if post.is_video else None
            youtube_links = self.extract_youtube_links(caption)
            
            data = InstagramReelData(
                caption=caption,
                media_url=media_url,
                posted_date=posted_date,
                video_url=video_url,
                youtube_links=youtube_links,
                shortcode=shortcode
            )
            
            logger.info(f"✅ Scraped post {shortcode}: {len(caption)} chars, {len(youtube_links)} YouTube links")
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to scrape {instagram_url}: {str(e)}")
            raise ValueError(f"Instagram scraping failed: {str(e)}")
