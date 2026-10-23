"""Gemini Blog Generator - Generate 800+ word blog articles using Gemini 3.5 Flash"""
import logging
import time
from google import genai
from google.genai import types
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class GeminiGenerator:
    def __init__(self, api_key: str, model_name: str = "gemini-3.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
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
You are a skilled content writer creating SEO-optimized blog posts for ameetpandey.com.

**Content Type**: {content_type}
**Instagram Caption**: 
{caption}

**Instructions**:
Write a comprehensive, in-depth blog article (MINIMUM 800 words, target 900-1000 words) based on the Instagram content above.

**Structure**:
1. **Catchy Title** - Create an SEO-friendly, engaging title
2. **Introduction** (120-150 words) - Hook the reader with the main idea, set expectations
3. **Main Content** (600-750 words) - Expand on the Instagram content with:
   - Clear explanations and detailed examples
   - Practical insights or actionable tips with step-by-step guidance
   - Personal anecdotes or relatable stories (if applicable)
   - Use subheadings (##) to organize sections (aim for 4-6 subheadings)
   - Add context, background, or supporting data where relevant
   - Include "why this matters" for each major point
4. **Conclusion** (80-100 words) - Summarize key takeaways and provide a call-to-action

**Tone**: Conversational, authentic, and engaging (like talking to a friend)

**CRITICAL**: The article MUST be at least 800 words. If the content seems short, add:
- More detailed explanations
- Additional examples or case studies
- Expanded context or background
- Deeper "how-to" steps
- Common mistakes to avoid
- FAQ-style subsections

**Special Instructions for {content_type}**:
"""
        
        type_specific = {
            "videos": "Focus on the video's key message. Add detailed summaries of each video. Include a '## Watch the Videos' section with placeholders [VIDEO_EMBED_1], [VIDEO_EMBED_2], etc. Explain why each video is valuable and what viewers will learn.",
            "books": "Highlight key lessons from the book with detailed explanations. Add a '## Get the Book' section with [AFFILIATE_PLACEHOLDER] for the book link. Include quotes or concepts from the book. Explain how to apply these lessons practically.",
            "products": "Explain the product's benefits and use cases in detail. Include [AFFILIATE_PLACEHOLDER] where relevant. Add pros/cons, comparison with alternatives, and specific use cases. Explain who this product is for.",
            "habits": "Provide step-by-step guidance on building the habit with detailed instructions. Include scientific backing if relevant. Add common pitfalls, troubleshooting tips, and progress tracking methods. Explain the psychology behind the habit.",
            "general": "Expand on the core message with substantial depth and practical examples. Add context, real-world applications, and actionable next steps. Include multiple perspectives or angles on the topic."
        }
        
        prompt = base_prompt + type_specific.get(content_type, type_specific["general"])
        prompt += "\n\n**Output Format**: Pure markdown. Start with # Title, then content sections. MINIMUM 800 WORDS."
        
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
                
                # Use new google-genai API
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                
                # Parse title and content
                markdown = response.text.strip()
                lines = markdown.split('\n', 1)
                
                title = lines[0].replace('# ', '').strip()
                content = lines[1].strip() if len(lines) > 1 else markdown
                
                word_count = len(content.split())
                logger.info(f"✅ Generated blog: {word_count} words, title: {title[:50]}...")
                
                # Warn if below 800 words (but don't fail)
                if word_count < 800:
                    logger.warning(f"⚠️  Word count below target: {word_count}/800 words")
                
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