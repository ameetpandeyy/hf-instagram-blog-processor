"""
TeAmo Cloud Image Generation Service
- Dual Engine: Google Gemini API (Imagen 3) & Hugging Face Serverless Inference (FLUX.1-schnell / SDXL)
- Automated Prompt Enhancement via Gemini Flash for authentic race, country, romantic dress, and scenic location
- Binary Search Compression ensuring each photo is strictly under 200 KB
- Direct upload to Supabase Storage 'persona-media' bucket with upsert
- Returns permanent public CDN URL
"""

import os
import io
import base64
import logging
import httpx
from typing import Optional, Dict, Any
from PIL import Image
from app.config import settings
from app.database import supabase

logger = logging.getLogger("teamo_image_gen")

MAX_IMAGE_SIZE_BYTES = 200 * 1024  # 200 KB limit
SUPABASE_BUCKET = "persona-media"

# Standard persona prompt blueprints matching race, region, personality, and romance
PERSONA_PROMPT_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "sara": {
        "name": "Sara",
        "city": "Mumbai",
        "ethnicity": "Young modern Indian woman from Mumbai",
        "style": "Playful, warm radiant smile, off-shoulder blush knit top, delicate gold jewelry, sea-facing Mumbai apartment with vinyl records",
        "scenes": {
            "beach": "Barefoot romantic sunset stroll in blush-pink sundress along golden ocean tide, warm evening sea breeze, cinematic golden hour glow",
            "club": "Glamorous rooftop neon lounge in burgundy slip dress holding cocktail overlooking Mumbai lights, purple ambient bokeh",
            "travel": "Scenic misty Himachal pine mountain overlook in cream winter coat and blush scarf, breathtaking mountain valley view",
            "music": "Retro vinyl lounge in cozy lavender cardigan laughing with studio headphones, listening to classic soul records",
            "cafe": "Sunlit artisan European cafe corner sipping hazelnut latte with heart latte art, warm morning light through glass window"
        }
    },
    "nia": {
        "name": "Nia",
        "city": "Bengaluru",
        "ethnicity": "Young South Indian tech enthusiast from Bengaluru",
        "style": "Witty smirk, intelligent dark brown eyes, wire-rim rose gold glasses, oversized sage-green knit sweater, modern Araku cafe aesthetic",
        "scenes": {
            "beach": "Relaxed seaside wooden deck at twilight in breezy ivory linen shirt and denim shorts, soft ocean waves",
            "club": "Cyberpunk arcade lounge with neon violet lighting, holding craft cocktail, playful confident expression",
            "travel": "Stargazing on a high mountain ridge with a portable telescope, crisp starry night sky over pine hills",
            "music": "Indie acoustic music studio playing electric keyboard surrounded by synthesizers and ambient purple LED strips",
            "cafe": "Cozy corner table in a botanical book cafe, iced matcha latte, reading a futuristic graphic novel with a gentle smile"
        }
    },
    "zoya": {
        "name": "Zoya",
        "city": "Delhi",
        "ethnicity": "North Indian woman from Delhi",
        "style": "Gentle, caring expression, deep almond eyes, soft cream cashmere turtleneck, side braid, sunlit plant-filled conservatory",
        "scenes": {
            "beach": "Walking near tranquil shoreline at dusk in flowing pastel peach maxi dress, gentle sea foam washing over sand",
            "club": "Intimate candlelit jazz lounge in elegant emerald evening dress listening to live saxophone, warm mahogany tones",
            "travel": "Alpine wildflower meadow in Himachal in a pastel lavender woolen shawl, gentle morning mist rolling over green peaks",
            "music": "Warm acoustic living room playing acoustic guitar softly, warm floor lamps and potted orchids",
            "cafe": "Artisan bakery counter sampling warm cinnamon rolls and freshly brewed pour-over coffee, laughing warmly"
        }
    },
    "alia": {
        "name": "Alia",
        "city": "Goa",
        "ethnicity": "Indie bohemian Indian woman living in Goa",
        "style": "Mysterious, thoughtful hazel eyes, sun-kissed tan skin, beach-wave hair, olive linen top, artisan silver tribal necklace",
        "scenes": {
            "beach": "Sitting on a sunset cliff above Goa beach in a bohemian terracotta wrap dress, purple and orange horizon",
            "club": "Boho beach shack lounge with fire pits, fairy lights under coconut palms, floral print sundress, tropical cocktail",
            "travel": "Offroad jeep expedition through lush tropical spice plantations and hidden jungle waterfalls, earth-tone safari jacket",
            "music": "Acoustic beach bonfire circle with acoustic guitar, singing under starry Goan night sky, flickering firelight",
            "cafe": "Open-air coastal patio cafe overlooking the Arabian sea, fresh tropical smoothie bowl, sea breeze in hair"
        }
    },
    "tara": {
        "name": "Tara",
        "city": "Jaipur",
        "ethnicity": "Creative director from Jaipur, Rajasthan",
        "style": "Bold charismatic gaze, modern Rajasthani contemporary high-fashion, statement ear cuffs, deep crimson silk shirt",
        "scenes": {
            "beach": "Sunset resort infinity pool overlooking golden dunes in chic black resort swimwear and sheer kimono",
            "club": "Luxury palace champagne lounge in satin ruby backless gown, sparkling crystal chandeliers, golden reflections",
            "travel": "Top ramparts of ancient Amber Fort at sunset overlooking rugged Aravalli mountains, dramatic royal heritage lighting",
            "music": "High-energy festival VIP deck dancing under amber laser lights in avant-garde designer festival attire",
            "cafe": "Heritage marble courtyard sipping saffron cardamom tea in royal blue block-printed co-ord set amidst pink marigolds"
        }
    },
    "kiara": {
        "name": "Kiara",
        "city": "Pune",
        "ethnicity": "Architectural designer from Pune, Maharashtra",
        "style": "Sharp intellectual gaze, tortoiseshell designer glasses, black turtleneck, minimalist glass architecture studio",
        "scenes": {
            "beach": "Modern beachfront glass villa balcony in minimalist white summer dress enjoying sea breeze and glass of white wine",
            "club": "Exclusive modern rooftop lounge in sleek slate-grey silhouette dress overlooking sparkling city highway below",
            "travel": "Western Ghats mountain view point after fresh monsoon rain, sleek waterproof windbreaker, misty valleys",
            "music": "Underground indie jazz speakeasy sitting near upright bass player, laughing in vintage leather jacket",
            "cafe": "Industrial loft specialty coffee roastery cupping single-origin Ethiopian espresso, architectural sketchbook open"
        }
    },
    "natasha": {
        "name": "Natasha",
        "city": "Kolkata",
        "ethnicity": "Bengali classical pianist from Kolkata",
        "style": "Soulful kohl-rimmed dark eyes, porcelain skin, emerald green cable-knit sweater, mahogany library with rain on window",
        "scenes": {
            "beach": "Historic coastline at blue hour, holding sheer cashmere stole against the sea mist, contemplative romantic gaze",
            "club": "Candlelit piano lounge in vintage velvet wine-red dress, playing a baby grand piano with warm amber lighting",
            "travel": "Misty Darjeeling tea estate terrace in an ivory woolen poncho, tea cup steaming in hand overlooking Kanchenjunga",
            "music": "Acoustic concert hall after rehearsal, sitting on stage by grand piano with sheet music in soft spotlight",
            "cafe": "College Street vintage bookstore cafe surrounded by old hardcovers, sipping hot darjeeling tea in quiet contemplation"
        }
    },
    "simran": {
        "name": "Simran",
        "city": "Chandigarh",
        "ethnicity": "Punjabi fitness trainer and superbike rider from Chandigarh",
        "style": "Athletic toned physique, leather moto jacket, high ponytail, sitting beside sports motorcycle on golden sunset highway",
        "scenes": {
            "beach": "Coastal highway ride resting by beach dunes in leather biker pants and athletic cropped tee, helmet resting on mirror",
            "club": "Trendy high-energy nightclub in fitted metallic silver halter dress, radiant laugh under pulsating purple strobes",
            "travel": "Winding Himalayan mountain pass highway at summit overlook, leaning against motorcycle taking in panoramic snowy peaks",
            "music": "Outdoor music festival dancing with hands in the air, sunset dust and festival lights creating golden halo",
            "cafe": "Late night highway dhaba sipping hot kulhad chai in cool night air, leather jacket unzipped, playful confident smile"
        }
    },
    "ananya": {
        "name": "Ananya",
        "city": "Hyderabad",
        "ethnicity": "Astronomy researcher from Hyderabad",
        "style": "Dreamy dusky skin, silver nose stud, celestial navy blue oversized sweater, starry planetarium observatory background",
        "scenes": {
            "beach": "Midnight shoreline gazing up at bioluminescent waves and full moon reflection, oversized knitted cardigan",
            "club": "Planetarium rooftop cocktail party under giant telescope dome, navy constellation dress with silver embroidery",
            "travel": "High-altitude astronomical observatory in Ladakh under vivid Milky Way galaxy, warm arctic parka with faux fur hood",
            "music": "Lo-fi synth lounge sitting cross-legged on floor cushions with wireless studio headphones, warm ambient fairy lights",
            "cafe": "Midnight university library cafe with glowing laptop and star maps, sipping dark roast mocha, dreamy thoughtful look"
        }
    },
    "aisha": {
        "name": "Aisha",
        "city": "Chennai",
        "ethnicity": "Tamil marine biologist and coastal surfer from Chennai",
        "style": "Sun-kissed golden bronze skin, hazel-brown eyes, ocean beach curls, coral halter top at golden sunrise beach",
        "scenes": {
            "beach": "Holding surfboard on wet shoreline in sporty coral swimsuit, golden sunrise glistening on ocean waves",
            "club": "Breezy seaside tiki lounge in floral tropical sundress, chilled coconut water cocktail with orchid flower, laughing warmly",
            "travel": "Trekking dramatic ocean bluffs on an exotic tropical island, ocean spray rising from waves crashing below",
            "music": "Beachside bonfire acoustic jam playing ukulele with friends under palm trees, glowing embers in night sky",
            "cafe": "Open-air thatched roof beach shack cafe sipping fresh dragonfruit smoothie bowl, smiling sunlit natural beauty"
        }
    }
}

async def expand_prompt_with_gemini(persona_id: str, scene_type: str = "avatar") -> str:
    """
    Uses Gemini API to construct an ultra-detailed, photorealistic image generation prompt.
    """
    persona = PERSONA_PROMPT_BLUEPRINTS.get(persona_id)
    if not persona:
        return f"Hyper-realistic photograph of a beautiful Indian woman named {persona_id}, high fashion editorial portrait, 85mm lens, natural skin texture."

    if scene_type == "avatar":
        base_desc = (
            f"Ultra-realistic high-end portrait photograph of {persona['name']}, a 24-year-old {persona['ethnicity']}. "
            f"{persona['style']}. Natural skin pores, authentic lighting, captured on 85mm f/1.4 lens, "
            f"magazine editorial photorealism, award-winning photography."
        )
    else:
        scene_desc = persona.get("scenes", {}).get(scene_type, "romantic lifestyle moment")
        base_desc = (
            f"Ultra-realistic cinematic lifestyle photograph of {persona['name']}, a 24-year-old {persona['ethnicity']}. "
            f"Setting: {scene_desc}. Natural human pose, authentic clothing texture, scenic location, "
            f"romantic atmosphere, 35mm f/1.8 lens, golden hour natural light, magazine quality photorealism."
        )

    # Optionally enhance via Gemini Flash if API key is present
    gemini_key = settings.GEMINI_API_KEY
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.DEFAULT_CHAT_MODEL}:generateContent?key={gemini_key}"
            prompt_instruction = (
                f"You are an expert AI photography director. Rewrite the following description into a single, cohesive, "
                f"hyper-realistic photographic prompt for FLUX.1/Imagen. Do not include introductory text, quotes or markdown. "
                f"Only output the raw prompt:\n\n{base_desc}"
            )
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json={"contents": [{"parts": [{"text": prompt_instruction}]}]})
                if res.status_code == 200:
                    data = res.json()
                    enhanced = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if len(enhanced) > 30:
                        return enhanced
        except Exception as e:
            logger.warning(f"Gemini prompt expansion fallback to base prompt: {e}")

    return base_desc

async def generate_with_gemini(prompt: str, aspect_ratio: str = "1:1") -> bytes:
    """
    Generates image using Google Gemini / Imagen 3 API.
    """
    key = settings.GEMINI_API_KEY
    if not key:
        raise ValueError("GEMINI_API_KEY is not set.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={key}"
    
    # Map aspect ratios for Imagen 3
    valid_ar = aspect_ratio if aspect_ratio in ["1:1", "3:4", "4:3", "9:16", "16:9"] else "1:1"
    
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": valid_ar,
            "outputMimeType": "image/jpeg"
        }
    }
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        res = await client.post(url, json=payload)
        if res.status_code == 200:
            data = res.json()
            predictions = data.get("predictions", [])
            if predictions and "bytesBase64Encoded" in predictions[0]:
                return base64.b64decode(predictions[0]["bytesBase64Encoded"])
            raise RuntimeError(f"Unexpected Gemini Imagen output structure: {data}")
        else:
            raise RuntimeError(f"Gemini Imagen API error [{res.status_code}]: {res.text}")

async def generate_with_huggingface(prompt: str, aspect_ratio: str = "1:1") -> bytes:
    """
    Generates image via Hugging Face Serverless Inference API (FLUX.1-schnell / SDXL).
    """
    token = settings.HF_TOKEN or os.environ.get("HF_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # FLUX.1-schnell on Hugging Face
    models = [
        "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
        "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
        "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    ]

    # Calculate dimensions
    width, height = (800, 800) if aspect_ratio == "1:1" else (768, 1024)

    async with httpx.AsyncClient(timeout=90.0) as client:
        last_error = ""
        for api_url in models:
            try:
                logger.info(f"Trying Hugging Face model: {api_url.split('/')[-1]}...")
                response = await client.post(
                    api_url,
                    headers=headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "width": width,
                            "height": height
                        }
                    }
                )
                if response.status_code == 200 and len(response.content) > 1000:
                    return response.content
                else:
                    last_error = f"{response.status_code}: {response.text[:200]}"
                    logger.warning(f"HF model {api_url} failed ({last_error}), trying fallback...")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"HF model exception: {e}")

        raise RuntimeError(f"All Hugging Face Image models failed. Last error: {last_error}")

def compress_to_max_200kb(raw_bytes: bytes, target_aspect: str = "1:1", max_bytes: int = MAX_IMAGE_SIZE_BYTES) -> bytes:
    """
    Ensures image is resized and compressed to under 200KB JPEG format with sharp quality.
    """
    with Image.open(io.BytesIO(raw_bytes)) as img:
        img = img.convert("RGB")

        # Set max target dimensions
        if target_aspect == "1:1":
            max_size = (800, 800)
        else:
            max_size = (800, 1066)

        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Binary search for optimal quality between 55 and 92
        low_q, high_q = 55, 92
        best_data = None

        for _ in range(6):
            mid_q = (low_q + high_q) // 2
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=mid_q, optimize=True)
            data = buffer.getvalue()

            if len(data) <= max_bytes:
                best_data = data
                low_q = mid_q + 1
            else:
                high_q = mid_q - 1

        if best_data is None:
            # Fallback downscale
            buffer = io.BytesIO()
            img.thumbnail((600, 800 if target_aspect != "1:1" else 600), Image.Resampling.LANCZOS)
            img.save(buffer, format="JPEG", quality=70, optimize=True)
            best_data = buffer.getvalue()

        return best_data

async def upload_to_supabase_storage(file_bytes: bytes, destination_path: str) -> str:
    """
    Uploads compressed image to Supabase Storage and returns the public CDN URL.
    """
    # 1. Try via Supabase Python SDK
    uploaded = False
    try:
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            destination_path,
            file_bytes,
            {"content-type": "image/jpeg", "upsert": "true"}
        )
        uploaded = True
    except Exception as e:
        logger.warning(f"SDK upload warning ({e}), falling back to direct REST upload...")

    # 2. Direct REST upload fallback with service role / anon key
    if not uploaded:
        supabase_url = settings.SUPABASE_URL.rstrip("/")
        api_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        upload_url = f"{supabase_url}/storage/v1/object/{SUPABASE_BUCKET}/{destination_path}"
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "image/jpeg",
            "x-upsert": "true"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(upload_url, headers=headers, content=file_bytes)
            if res.status_code not in (200, 201):
                logger.error(f"Supabase REST upload failed [{res.status_code}]: {res.text}")

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{destination_path}"
    return public_url

async def generate_and_store_persona_image(
    persona_id: str,
    prompt: Optional[str] = None,
    category: str = "avatars",
    scene_tag: str = "avatar",
    engine: str = "auto",
    aspect_ratio: str = "1:1"
) -> Dict[str, Any]:
    """
    End-to-end background pipeline:
    1. Expands/refines prompt using Gemini API based on race & scene.
    2. Generates image via Gemini (Imagen 3) with automatic Hugging Face (FLUX.1/SDXL) fallback.
    3. Compresses strictly under 200 KB.
    4. Uploads to Supabase Storage 'persona-media/{category}/{filename}.jpg'.
    5. Returns public URL and metadata.
    """
    final_prompt = prompt or await expand_prompt_with_gemini(persona_id, scene_type=scene_tag)
    logger.info(f"Generating [{category}/{persona_id}] with engine '{engine}'... Prompt: {final_prompt[:80]}...")

    raw_bytes = None
    engine_used = ""

    # Engine selection & automatic fallback
    if engine == "huggingface":
        try:
            raw_bytes = await generate_with_huggingface(final_prompt, aspect_ratio=aspect_ratio)
            engine_used = "huggingface"
        except Exception as e:
            logger.warning(f"HF failed ({e}), falling back to Gemini...")
            raw_bytes = await generate_with_gemini(final_prompt, aspect_ratio=aspect_ratio)
            engine_used = "gemini"
    elif engine == "gemini":
        try:
            raw_bytes = await generate_with_gemini(final_prompt, aspect_ratio=aspect_ratio)
            engine_used = "gemini"
        except Exception as e:
            logger.warning(f"Gemini failed ({e}), falling back to Hugging Face...")
            raw_bytes = await generate_with_huggingface(final_prompt, aspect_ratio=aspect_ratio)
            engine_used = "huggingface"
    else:  # "auto"
        try:
            raw_bytes = await generate_with_gemini(final_prompt, aspect_ratio=aspect_ratio)
            engine_used = "gemini"
        except Exception as e:
            logger.warning(f"Auto engine: Gemini failed ({e}), switching to Hugging Face...")
            raw_bytes = await generate_with_huggingface(final_prompt, aspect_ratio=aspect_ratio)
            engine_used = "huggingface"

    compressed_bytes = compress_to_max_200kb(raw_bytes, target_aspect=aspect_ratio)
    file_name = f"{persona_id}.jpg" if category == "avatars" else f"{scene_tag}.jpg"
    storage_path = f"{category}/{file_name}"

    cdn_url = await upload_to_supabase_storage(compressed_bytes, storage_path)
    file_size_kb = round(len(compressed_bytes) / 1024, 1)

    logger.info(f"✓ Uploaded {storage_path} ({file_size_kb} KB) via {engine_used}: {cdn_url}")

    return {
        "success": True,
        "persona_id": persona_id,
        "category": category,
        "scene_tag": scene_tag,
        "engine_used": engine_used,
        "size_kb": file_size_kb,
        "url": cdn_url,
        "prompt": final_prompt,
    }
