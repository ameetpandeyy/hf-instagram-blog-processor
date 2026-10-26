import json
import logging
from typing import List, Dict, Any
from google import genai
from app.config import settings
from app.database import get_supabase

logger = logging.getLogger(__name__)

def get_gemini_client() -> genai.Client:
    return genai.Client(api_key=settings.GEMINI_API_KEY or "dummy_key")

async def get_user_memories(user_id: str, persona_id: str, limit: int = 4) -> List[str]:
    """
    Fetches the top 4 most durable personal facts extracted about the user to keep prompt context short and cheap.
    """
    try:
        supabase = get_supabase()
        res = (
            supabase.table("memory")
            .select("fact")
            .eq("user_id", user_id)
            .eq("persona_id", persona_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        if res.data:
            return [row["fact"] for row in res.data]
    except Exception as e:
        logger.warning(f"Could not load memories from Supabase: {e}")
    return []

async def extract_and_save_facts(user_id: str, persona_id: str, recent_messages: List[Dict[str, str]]):
    """
    Cheap async fact extraction using Gemini 2.0 Flash.
    Only called periodically (every ~10 messages) to save cost.
    """
    if len(recent_messages) < 4 or not settings.GEMINI_API_KEY:
        return

    dialogue = "\n".join([f"{m.get('sender', 'user')}: {m.get('content', '')}" for m in recent_messages[-8:]])

    extraction_prompt = f"""You are an efficient memory extractor for an AI companion.
Analyze the following conversation dialogue and extract 1 or 2 durable, concrete facts about the user (e.g., location, hobbies, favorites, pets, occupation).
DO NOT include temporary chit-chat, greetings, or explicit content.

Conversation:
{dialogue}

Respond ONLY with valid JSON in this exact structure:
{{"facts": ["fact 1", "fact 2"]}}
If no new durable personal facts are revealed, respond with:
{{"facts": []}}
"""
    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=settings.MEMORY_EXTRACTION_MODEL,
            contents=extraction_prompt,
        )
        raw_text = response.text.strip()
        # Clean markdown code blocks if returned
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        parsed = json.loads(raw_text.strip())
        facts = parsed.get("facts", [])

        if facts:
            supabase = get_supabase()
            for fact in facts:
                if len(fact.strip()) > 5:
                    supabase.table("memory").insert({
                        "user_id": user_id,
                        "persona_id": persona_id,
                        "fact": fact.strip(),
                        "source": "Chat extraction",
                    }).execute()
            logger.info(f"Saved {len(facts)} extracted memories for user {user_id}")
    except Exception as e:
        logger.warning(f"Background fact extraction failed: {e}")
