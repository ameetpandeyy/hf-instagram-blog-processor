import logging
from typing import Dict, Any, List
from google import genai
from google.genai import types
from app.config import settings
from app.database import get_supabase
from app.safety import check_pre_llm_safety, check_post_llm_safety
from app.memory import get_user_memories, extract_and_save_facts

logger = logging.getLogger(__name__)

async def generate_chat_reply(
    user: Dict[str, Any],
    persona_id: str,
    user_message: str,
    recent_history: List[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Generates cost-optimized, low-latency companion response using Gemini 2.0 Flash.
    Enforces safety filters and injects durable memories.
    """
    user_id = str(user.get("id", ""))
    supabase = get_supabase()

    # 1. Pre-LLM Safety Verification (Minors, self-harm, severe violations)
    is_safe, flag_type, safety_msg = check_pre_llm_safety(user_message)
    if not is_safe:
        # Save message with flag
        try:
            supabase.table("messages").insert({
                "user_id": user_id,
                "persona_id": persona_id,
                "sender_type": "user",
                "content": user_message,
                "safety_flag": flag_type,
            }).execute()
        except Exception:
            pass

        return {
            "reply": safety_msg,
            "safety_flag": flag_type,
            "end_chat": flag_type == "minor_signal",
            "tokens_used": 0,
        }

    # 2. Fetch Persona definition
    persona = None
    try:
        res = supabase.table("personas").select("*").eq("id", persona_id).execute()
        if res.data and len(res.data) > 0:
            persona = res.data[0]
    except Exception as e:
        logger.warning(f"Error fetching persona {persona_id}: {e}")

    if not persona:
        persona = {
            "name": "Sara",
            "age": 24,
            "vibe": "Playful and warm",
            "languages": ["Hinglish"],
            "system_prompt": "You are Sara, a 24-year-old adult AI companion. You speak natural Hinglish, are playful and flirty but non-explicit.",
        }

    # 3. Retrieve user memories for context injection (keeps token cost minimal)
    memories = await get_user_memories(user_id, persona_id, limit=3)
    memory_str = "; ".join(memories) if memories else "None yet"

    user_name = user.get("display_name", "Alex")
    interests_str = ", ".join(user.get("interests", ["Music", "Movies"]))
    language = user.get("language_pref", "Hinglish")

    system_instruction = f"""{persona.get('system_prompt', '')}

Always be transparent that you are an AI if asked.
USER INFO: Name: {user_name}, Interests: {interests_str}, Language: {language}
DURABLE MEMORIES: {memory_str}
RESPONSE STYLE: 1-3 short texter-style sentences. Mirror their tone. End with one easy question or playful hook. Flirty and romantic, NOT sexually explicit.
STRICT RULES: Never guilt, pressure, or pretend to be jealous. Never mention money or ask to pay. If they say they are under 18, immediately terminate the chat.
"""

    # 4. Call Gemini 2.0 Flash
    reply_text = ""
    tokens_used = 0

    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            # Format dialogue context
            contents = []
            if recent_history:
                for m in recent_history[-6:]:
                    role = "user" if m.get("sender") == "user" else "model"
                    contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m.get("content", ""))]))
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.85,
                max_output_tokens=150,
            )

            response = client.models.generate_content(
                model=settings.DEFAULT_CHAT_MODEL,
                contents=contents,
                config=config,
            )
            reply_text = response.text.strip()
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens_used = response.usage_metadata.total_token_count or 80
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            reply_text = "Hey! I got a little distracted for a second, but I'm all yours now. What were you saying? 😊"
    else:
        # Fallback simulator when API key is not yet set
        reply_text = f"Haha {user_name}, you always know how to make me smile! What else are you up to tonight? 😊"

    # 5. Post-LLM verification & sanitization
    reply_text = check_post_llm_safety(reply_text)

    # 6. Save messages to Supabase audit trail
    try:
        supabase.table("messages").insert([
            {"user_id": user_id, "persona_id": persona_id, "sender_type": "user", "content": user_message},
            {"user_id": user_id, "persona_id": persona_id, "sender_type": "ai", "content": reply_text, "tokens_used": tokens_used},
        ]).execute()
    except Exception as e:
        logger.warning(f"Could not persist messages to Supabase: {e}")

    # 7. Asynchronous fact extraction (non-blocking)
    if recent_history and len(recent_history) % 8 == 0:
        history_copy = list(recent_history) + [{"sender": "user", "content": user_message}]
        import asyncio
        asyncio.create_task(extract_and_save_facts(user_id, persona_id, history_copy))

    return {
        "reply": reply_text,
        "safety_flag": "clean",
        "end_chat": False,
        "tokens_used": tokens_used,
    }
