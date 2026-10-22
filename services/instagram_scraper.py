"""Instagram Scraper - Extract content from Instagram posts"""
import re
import logging
import ssl
import certifi
from typing import Optional, Dict, List
from dataclasses import dataclass
import instaloader
import urllib3

logger = logging.getLogger(__name__)

# Disable SSL warnings (for environments with certificate issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        # Configure SSL context with certifi certificates
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        except Exception as e:
            logger.warning(f"Failed to create secure SSL context: {e}")
            # Fallback to less strict SSL
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True,
            max_connection_attempts=3
        )
        
        # Set custom user agent to avoid blocks
        self.loader.context._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        logger.info("Instagram scraper initialized with SSL handling")
    
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
            
            # Load post without authentication (with retries built into instaloader)
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
            error_msg = str(e)
            logger.error(f"❌ Failed to scrape {instagram_url}: {error_msg}")
            
            # Provide helpful error message
            if 'SSL' in error_msg or 'ssl' in error_msg:
                raise ValueError(f"SSL certificate error when scraping Instagram. This may be due to the HuggingFace Space environment. Error: {error_msg}")
            elif '429' in error_msg or 'rate limit' in error_msg.lower():
                raise ValueError(f"Instagram rate limit reached. Please wait before retrying. Error: {error_msg}")
            elif '404' in error_msg:
                raise ValueError(f"Instagram post not found. URL may be invalid or post was deleted. Error: {error_msg}")
            else:
                raise ValueError(f"Instagram scraping failed: {error_msg}")
