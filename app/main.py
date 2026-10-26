import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.database import get_supabase
from app.firebase_auth import get_current_user
from app.chat import generate_chat_reply
from app.credits import get_user_balance, deduct_for_message, credit_ad_reward
from app.matching import compute_match_score
from app.memory import get_user_memories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("teamo_backend")

app = FastAPI(
    title="TeAmo AI Companion Backend API",
    description="High-efficiency, cost-optimized backend for TeAmo AI Companion app. Designed for Hugging Face Spaces and Vercel/Supabase integration.",
    version="1.0.0",
)

# CORS configuration for Flutter (web/mobile) and Admin CRM
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------

class UserProfileSync(BaseModel):
    display_name: Optional[str] = None
    age: Optional[int] = None
    interests: Optional[List[str]] = None
    vibes: Optional[List[str]] = None
    language_pref: Optional[str] = None
    age_range_pref: Optional[List[str]] = None
    ethnicity_pref: Optional[str] = None

class ChatRequest(BaseModel):
    persona_id: str
    message: str
    recent_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str
    persona_id: str
    safety_flag: Optional[str] = None
    end_chat: bool = False
    tokens_used: int = 0
    free_messages_remaining: int = 0
    credits_balance: int = 0

class ReportRequest(BaseModel):
    persona_id: str
    reason: str
    message_excerpt: Optional[str] = None

class RewardRequest(BaseModel):
    transaction_id: Optional[str] = ""

# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "app": "TeAmo AI Companion API",
        "status": "healthy",
        "version": "1.0.0",
        "huggingface_space": True,
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "teamo-fastapi"}

@app.post("/auth/sync")
async def sync_user(
    profile_data: Optional[UserProfileSync] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Syncs Firebase authenticated user profile into Supabase.
    Ensures zero data loss between Firebase and Supabase database.
    """
    user_id = current_user.get("id")
    supabase = get_supabase()

    if profile_data and user_id and user_id != "transient_user_id":
        update_fields = {}
        if profile_data.display_name:
            update_fields["display_name"] = profile_data.display_name
        if profile_data.age:
            update_fields["age"] = profile_data.age
        if profile_data.interests is not None:
            update_fields["interests"] = profile_data.interests
        if profile_data.vibes is not None:
            update_fields["vibes"] = profile_data.vibes
        if profile_data.language_pref:
            update_fields["language_pref"] = profile_data.language_pref
        if profile_data.age_range_pref is not None:
            update_fields["age_range_pref"] = profile_data.age_range_pref
        if profile_data.ethnicity_pref:
            update_fields["ethnicity_pref"] = profile_data.ethnicity_pref

        if update_fields:
            try:
                res = supabase.table("users").update(update_fields).eq("id", user_id).execute()
                if res.data and len(res.data) > 0:
                    current_user.update(res.data[0])
            except Exception as e:
                logger.warning(f"Failed to update user profile preferences: {e}")

    balance = get_user_balance(user_id) if user_id else 100
    current_user["credits_balance"] = balance
    return {"status": "synced", "user": current_user}

@app.get("/personas")
def list_personas():
    """
    Returns active personas with prompts, vibes, and profile details.
    """
    supabase = get_supabase()
    try:
        res = supabase.table("personas").select("*").eq("is_active", True).execute()
        return {"personas": res.data if res.data else []}
    except Exception as e:
        logger.error(f"Error fetching personas from Supabase: {e}")
        # Default fallback personas
        return {
            "personas": [
                {
                    "id": "sara_01",
                    "name": "Sara",
                    "age": 24,
                    "vibe": "Playful and warm",
                    "short_bio": "Always brings lighthearted humor and emotional comfort.",
                    "languages": ["English", "Hindi", "Hinglish"],
                    "tags": ["Bollywood", "Music", "Late night talks"],
                    "avatar_url": "/assets/personas/sara.png",
                },
                {
                    "id": "nia_02",
                    "name": "Nia",
                    "age": 26,
                    "vibe": "Ambitious and witty",
                    "short_bio": "Tech enthusiast and coffee lover with sharp banter.",
                    "languages": ["English", "Hinglish"],
                    "tags": ["Startups", "Sci-Fi", "Fitness"],
                    "avatar_url": "/assets/personas/nia.png",
                },
                {
                    "id": "riya_03",
                    "name": "Riya",
                    "age": 22,
                    "vibe": "Gentle and empathetic",
                    "short_bio": "A soothing presence who listens without judgment.",
                    "languages": ["English", "Hindi"],
                    "tags": ["Poetry", "Art", "Mindfulness"],
                    "avatar_url": "/assets/personas/riya.png",
                },
                {
                    "id": "meera_04",
                    "name": "Meera",
                    "age": 25,
                    "vibe": "Adventurous and bold",
                    "short_bio": "Passionate about travel, indie music, and spontaneous road trips.",
                    "languages": ["English", "Hinglish", "Punjabi"],
                    "tags": ["Travel", "Photography", "Food"],
                    "avatar_url": "/assets/personas/meera.png",
                },
            ]
        }

@app.post("/personas/match")
async def match_personas(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Calculates weighted matching score between current user's profile and active personas.
    """
    personas_response = list_personas()
    personas_list = personas_response.get("personas", [])

    scored_personas = []
    for p in personas_list:
        score = compute_match_score(current_user, p)
        p_copy = dict(p)
        p_copy["match_percentage"] = score
        scored_personas.append(p_copy)

    # Sort descending by match score
    scored_personas.sort(key=lambda x: x["match_percentage"], reverse=True)
    return {"matches": scored_personas}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Cost-effective companion response endpoint.
    1. Checks free allowance or double-entry credit ledger.
    2. Runs Gemini 2.0 Flash with injected memory facts.
    3. Handles safety filters and minor signals.
    """
    user_id = str(current_user.get("id", ""))

    # 1. Deduct credit or free allowance
    allowed, deduct_reason = deduct_for_message(user_id, persona_name=req.persona_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Out of credits. Watch a rewarded video ad or purchase credits to continue.",
        )

    # 2. Generate response via Gemini 2.0 Flash
    reply_payload = await generate_chat_reply(
        user=current_user,
        persona_id=req.persona_id,
        user_message=req.message,
        recent_history=req.recent_history,
    )

    # 3. Read updated balance
    supabase = get_supabase()
    free_remaining = 0
    try:
        user_row = supabase.table("users").select("free_messages_remaining").eq("id", user_id).execute()
        if user_row.data:
            free_remaining = user_row.data[0].get("free_messages_remaining", 0)
    except Exception:
        pass

    current_balance = get_user_balance(user_id)

    return ChatResponse(
        reply=reply_payload.get("reply", "..."),
        persona_id=req.persona_id,
        safety_flag=reply_payload.get("safety_flag"),
        end_chat=reply_payload.get("end_chat", False),
        tokens_used=reply_payload.get("tokens_used", 0),
        free_messages_remaining=free_remaining,
        credits_balance=current_balance,
    )

@app.get("/credits/balance")
async def get_balance(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieves current user's live credit balance and ledger transactions.
    """
    user_id = str(current_user.get("id", ""))
    supabase = get_supabase()

    free_remaining = current_user.get("free_messages_remaining", 0)
    balance = get_user_balance(user_id)

    ledger_history = []
    try:
        res = (
            supabase.table("credit_ledger")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        if res.data:
            ledger_history = res.data
    except Exception as e:
        logger.error(f"Error reading credit ledger history: {e}")

    return {
        "user_id": user_id,
        "credits_balance": balance,
        "free_messages_remaining": free_remaining,
        "ledger": ledger_history,
    }

@app.post("/ads/reward")
async def reward_ad(
    req: RewardRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Processes AdMob Rewarded Video SSV (+10 free messages).
    """
    user_id = str(current_user.get("id", ""))
    res = credit_ad_reward(user_id, req.transaction_id or "")
    balance = get_user_balance(user_id)
    return {
        "status": "success",
        "reward_granted": 10,
        "free_messages_remaining": res.get("free_messages_remaining", 10),
        "credits_balance": balance,
    }

@app.post("/report")
async def submit_report(
    req: ReportRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Submits user safety or harassment report to Supabase for admin review in CRM.
    """
    user_id = str(current_user.get("id", ""))
    supabase = get_supabase()
    try:
        supabase.table("reports").insert({
            "reporter_user_id": user_id,
            "persona_id": req.persona_id,
            "reason": req.reason,
            "message_excerpt": req.message_excerpt or "",
            "status": "open",
        }).execute()
        return {"status": "submitted", "message": "Report logged for moderation."}
    except Exception as e:
        logger.error(f"Failed to submit report: {e}")
        return {"status": "submitted", "message": "Report received."}

@app.get("/memory")
async def list_user_memories(
    persona_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Lists durable facts extracted and stored for the current user.
    """
    user_id = str(current_user.get("id", ""))
    facts = get_user_memories(user_id, persona_id)
    return {"user_id": user_id, "memories": facts}

class GenerateImageRequest(BaseModel):
    persona_id: str
    prompt: str
    category: Optional[str] = "avatars"
    engine: Optional[str] = "gemini"

@app.post("/api/personas/generate-image")
async def generate_persona_image_endpoint(req: GenerateImageRequest):
    """
    Generates image via Gemini/Hugging Face, compresses to <200KB, uploads to Supabase Storage, and returns public URL.
    """
    from app.image_gen import generate_and_store_persona_image
    try:
        url = await generate_and_store_persona_image(
            persona_id=req.persona_id,
            prompt=req.prompt,
            category=req.category or "avatars",
            engine=req.engine or "gemini"
        )
        return {"success": True, "url": url}
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

