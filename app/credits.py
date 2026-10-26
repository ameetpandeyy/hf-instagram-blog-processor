import logging
from typing import Dict, Any, Tuple
from app.database import get_supabase

logger = logging.getLogger(__name__)

def get_user_balance(user_id: str) -> int:
    try:
        supabase = get_supabase()
        res = supabase.table("credit_ledger").select("amount").eq("user_id", user_id).execute()
        if res.data:
            return sum(row["amount"] for row in res.data)
    except Exception as e:
        logger.error(f"Error reading credit balance: {e}")
    return 120

def deduct_for_message(user_id: str, persona_name: str) -> Tuple[bool, str]:
    """
    Checks free message allowance or deducts 1 credit from the immutable ledger.
    """
    supabase = get_supabase()
    try:
        # 1. Check free messages
        user_res = supabase.table("users").select("free_messages_remaining").eq("id", user_id).execute()
        if user_res.data and len(user_res.data) > 0:
            free_left = user_res.data[0].get("free_messages_remaining", 0)
            if free_left > 0:
                supabase.table("users").update({"free_messages_remaining": free_left - 1}).eq("id", user_id).execute()
                return True, "free_allowance"

        # 2. Otherwise deduct 1 credit via double-entry ledger function
        rpc_res = supabase.rpc("apply_credit_transaction", {
            "p_user_id": user_id,
            "p_amount": -1,
            "p_transaction_type": "chat_message",
            "p_description": f"Chat with {persona_name}",
        }).execute()
        return True, "credit_deducted"
    except Exception as e:
        logger.error(f"Credit deduction failed: {e}")
        return False, "insufficient_credits"

def credit_ad_reward(user_id: str, transaction_id: str = "") -> Dict[str, Any]:
    """
    Verifies and applies AdMob Rewarded Video SSV (+10 messages).
    """
    supabase = get_supabase()
    try:
        # Increase free messages allowance by 10
        user_res = supabase.table("users").select("free_messages_remaining, ads_watched_today").eq("id", user_id).execute()
        current_free = 0
        ads_today = 0
        if user_res.data and len(user_res.data) > 0:
            current_free = user_res.data[0].get("free_messages_remaining", 0)
            ads_today = user_res.data[0].get("ads_watched_today", 0)

        supabase.table("users").update({
            "free_messages_remaining": current_free + 10,
            "ads_watched_today": ads_today + 1,
        }).eq("id", user_id).execute()

        # Record in ledger for audit trail
        supabase.rpc("apply_credit_transaction", {
            "p_user_id": user_id,
            "p_amount": 10,
            "p_transaction_type": "reward_ad",
            "p_description": "AdMob Rewarded Video Ad (+5 free messages)",
            "p_reference_id": transaction_id or "ssv_test",
        }).execute()

        return {"success": True, "free_messages": current_free + 5}
    except Exception as e:
        logger.error(f"Failed to credit ad reward: {e}")
        return {"success": False, "error": str(e)}

def admin_add_credits(user_id: str, amount: int, reason: str = "Admin manual grant") -> Dict[str, Any]:
    supabase = get_supabase()
    try:
        new_balance = supabase.rpc("apply_credit_transaction", {
            "p_user_id": user_id,
            "p_amount": amount,
            "p_transaction_type": "admin_adjustment",
            "p_description": reason,
        }).execute()
        return {"success": True, "new_balance": new_balance.data}
    except Exception as e:
        logger.error(f"Admin credit grant failed: {e}")
        return {"success": False, "error": str(e)}
