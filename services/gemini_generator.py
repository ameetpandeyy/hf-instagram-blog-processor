"""Gemini Blog Generator - Generate 600-word blog articles"""
import logging
import time
import google.generativeai as genai
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class GeminiGenerator:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash-latest"):
        genai.configure(api_key=api_key)
        # Use the correct model name format
        self.model = genai.GenerativeModel(model_name)
        self.rpm_limit = 15
        self.last_request_time = 0
        logger.info(f"Gemini generator initialized: {model_name}")
    
    def _rate_limit(self):
        """Implement rate limiting (15 RPM)"""
        min_interval = 60.0 / self.rpm_limit  # 4 seconds
        elapsed = time.time() - self.last_request_time
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _build_prompt(self, caption: str, content_type: str) -> str:
        """Build optimized prompt based on content type"""
        
        base_prompt = f"""
You are a skilled content writer creating engaging blog posts for ameetpandey.com.

**Content Type**: {content_type}
**Instagram Caption**: 
{caption}

**Instructions**:
Write a comprehensive blog article (approximately 600 words) based on the Instagram content above.

**Structure**:
1. **Catchy Title** - Create an SEO-friendly, engaging title
2. **Introduction** (80-100 words) - Hook the reader with the main idea
3. **Main Content** (400-450 words) - Expand on the Instagram content with:
   - Clear explanations and examples
   - Practical insights or actionable tips
   - Personal anecdotes or relatable stories (if applicable)
   - Use subheadings (##) to organize sections
4. **Conclusion** (50-70 words) - Summarize key takeaways

**Tone**: Conversational, authentic, and engaging (like talking to a friend)

**Special Instructions for {content_type}**:
"""
        
        type_specific = {
            "videos": "Focus on the video's key message. Add a '## Watch the Video' section with placeholder [VIDEO_EMBED]",
            "books": "Highlight key lessons from the book. Add a '## Get the Book' section with [AFFILIATE_PLACEHOLDER] for the book link",
            "products": "Explain the product's benefits and use cases. Include [AFFILIATE_PLACEHOLDER] where relevant",
            "habits": "Provide step-by-step guidance on building the habit. Include scientific backing if relevant",
            "general": "Expand on the core message with depth and practical examples"
        }
        
        prompt = base_prompt + type_specific.get(content_type, type_specific["general"])
        prompt += "\n\n**Output Format**: Pure markdown. Start with # Title, then content sections."
        
        return prompt
    
    async def generate_blog(
        self,
        caption: str,
        content_type: str = "general",
        retries: int = 3
    ) -> Dict[str, str]:
        """
        Generate blog article from Instagram caption
        
        Args:
            caption: Instagram post caption
            content_type: Content category (videos, books, products, habits, general)
            retries: Number of retry attempts on failure
        
        Returns:
            Dict with 'title' and 'content' (markdown)
        
        Raises:
            Exception: If generation fails after all retries
        """
        prompt = self._build_prompt(caption, content_type)
        
        for attempt in range(retries):
            try:
                self._rate_limit()
                
                logger.info(f"Generating blog (attempt {attempt + 1}/{retries}, type: {content_type})")
                
                response = self.model.generate_content(prompt)
                
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                
                # Parse title and content
                markdown = response.text.strip()
                lines = markdown.split('\n', 1)
                
                title = lines[0].replace('# ', '').strip()
                content = lines[1].strip() if len(lines) > 1 else markdown
                
                word_count = len(content.split())
                logger.info(f"✅ Generated blog: {word_count} words, title: {title[:50]}...")
                
                return {
                    "title": title,
                    "content": content,
                    "word_count": word_count
                }
                
            except Exception as e:
                logger.warning(f"⚠️  Generation attempt {attempt + 1} failed: {str(e)}")
                if attempt == retries - 1:
                    logger.error(f"❌ All {retries} generation attempts failed")
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("Blog generation failed after all retries")
