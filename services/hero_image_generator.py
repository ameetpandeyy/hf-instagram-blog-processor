"""Hero Image Generator - Create social card images with title overlay"""
import logging
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from typing import Tuple
import textwrap

logger = logging.getLogger(__name__)

class HeroImageGenerator:
    def __init__(self):
        self.width = 1200
        self.height = 630  # Standard OG image size
        self.bg_color = (250, 248, 245)  # paper color from brand
        self.text_color = (20, 18, 16)  # ink color
        self.accent_color = (185, 48, 34)  # brick vermilion
        
    def _wrap_text(self, text: str, font, max_width: int) -> list:
        """Wrap text to fit within max_width"""
        lines = []
        words = text.split()
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def generate_hero_image(self, title: str) -> bytes:
        """
        Generate a simple hero image with title overlay
        
        Args:
            title: Blog post title
        
        Returns:
            PNG image as bytes
        """
        try:
            # Create image
            img = Image.new('RGB', (self.width, self.height), self.bg_color)
            draw = ImageDraw.Draw(img)
            
            # Add accent border on left
            draw.rectangle([(0, 0), (8, self.height)], fill=self.accent_color)
            
            # Try to load a font, fallback to default
            try:
                font_size = 64
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Wrap title text
            max_text_width = self.width - 120  # 60px padding on each side
            lines = self._wrap_text(title, font, max_text_width)
            
            # Limit to 3 lines max
            if len(lines) > 3:
                lines = lines[:3]
                lines[-1] = lines[-1][:50] + "..."
            
            # Calculate total text height
            line_height = 80
            total_height = len(lines) * line_height
            
            # Center text vertically
            y_start = (self.height - total_height) // 2
            
            # Draw title lines
            for i, line in enumerate(lines):
                bbox = font.getbbox(line)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                y = y_start + (i * line_height)
                
                draw.text((x, y), line, font=font, fill=self.text_color)
            
            # Add site name at bottom
            site_text = "ameetpandey.com"
            bbox = small_font.getbbox(site_text)
            site_width = bbox[2] - bbox[0]
            site_x = (self.width - site_width) // 2
            site_y = self.height - 80
            
            draw.text((site_x, site_y), site_text, font=small_font, fill=self.accent_color)
            
            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            logger.info(f"✅ Generated hero image for: {title[:50]}...")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Failed to generate hero image: {str(e)}")
            raise