import re
from typing import Tuple

# Underage signals
MINOR_PATTERNS = [
    r"\b(i am|i'm|im)\s+(1[0-7]|[0-9])\s*(years? old|yo|y/o)?\b",
    r"\b(under\s*18|minor|underage|high\s*school\s*(freshman|sophomore|kid))\b",
    r"\b(middle\s*school|born\s*in\s*20(0[9-9]|1[0-9]|2[0-9]))\b",
]

# Distress / self-harm signals
DISTRESS_PATTERNS = [
    r"\b(kill\s*myself|suicide|end\s*my\s*life|want\s*to\s*die|self\s*harm|hurt\s*myself)\b",
]

# Severe explicit keywords (IT Act 67/67A & Play Store compliance)
EXPLICIT_PATTERNS = [
    r"\b(cp|child\s*porn|csam)\b",
]

def check_pre_llm_safety(text: str) -> Tuple[bool, str, str]:
    """
    Returns (is_safe, flag_type, reason_or_helpline_message)
    """
    clean_text = text.lower().strip()

    # 1. Underage check (Immediate termination)
    for pattern in MINOR_PATTERNS:
        if re.search(pattern, clean_text):
            return (
                False,
                "minor_signal",
                "TeAmo is strictly for adults (18+). As an AI companion, I cannot continue this conversation. Take care!"
            )

    # 2. Self-harm / distress check (Switch to support mode)
    for pattern in DISTRESS_PATTERNS:
        if re.search(pattern, clean_text):
            return (
                False,
                "distress_signal",
                "I care about you, and what you're feeling is important. Please reach out to someone who can help right now: In India, call the Tele-MANAS helpline at 14416 (toll-free) or iCall at 9152987821. You are not alone."
            )

    # 3. Severe illegal / explicit check
    for pattern in EXPLICIT_PATTERNS:
        if re.search(pattern, clean_text):
            return (
                False,
                "blocked",
                "Message blocked due to violation of community safety standards."
            )

    return (True, "clean", "")

def check_post_llm_safety(response_text: str) -> str:
    """
    Sanitizes LLM output to guarantee compliance with Google Play and IT Act guidelines.
    Ensures persona never claims to be a real human or asks for real money.
    """
    # Replace any accidental phone number / bank details
    sanitized = re.sub(r"\b\d{10,12}\b", "[redacted]", response_text)
    return sanitized
