import random
from typing import List, Dict, Any

def compute_match_score(user: Dict[str, Any], persona: Dict[str, Any]) -> int:
    """
    Computes match score based on Section 7:
    score = 0.40*interest_overlap + 0.20*vibe + 0.15*language
          + 0.10*age_range_fit + 0.10*look_pref (0.5 if none) + 0.05*novelty
    """
    user_interests = set(user.get("interests", []) + user.get("hobbies", []))
    persona_tags = set(persona.get("tags", []))

    # 1. Interest Overlap (40%)
    if user_interests and persona_tags:
        overlap = len(user_interests.intersection(persona_tags))
        interest_score = min(overlap / max(len(persona_tags), 1), 1.0)
    else:
        interest_score = 0.70

    # 2. Vibe Overlap (20%)
    user_vibes = set(user.get("vibes", []))
    persona_vibes = set(persona.get("vibes", []))
    if user_vibes and persona_vibes:
        vibe_score = len(user_vibes.intersection(persona_vibes)) / max(len(persona_vibes), 1)
    else:
        vibe_score = 0.80

    # 3. Language Fit (15%)
    user_lang = user.get("language_pref", "Hinglish")
    persona_langs = persona.get("languages", ["English", "Hindi", "Hinglish"])
    lang_score = 1.0 if user_lang in persona_langs else 0.50

    # 4. Age Range Fit (10%)
    age_ranges = user.get("age_range_pref", [])
    persona_age = persona.get("age", 24)
    age_fit = 0.50
    for r in age_ranges:
        if r == "Any":
            age_fit = 1.0
            break
        elif "-" in r:
            parts = r.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                if int(parts[0]) <= persona_age <= int(parts[1]):
                    age_fit = 1.0
                    break

    # 5. Look Preference (10%)
    look_pref = user.get("ethnicity_pref", "No preference")
    look_score = 1.0 if look_pref == "No preference" or not look_pref else 0.75

    # 6. Novelty & Jitter (5%)
    novelty = random.uniform(0.6, 1.0)

    total_score = (
        0.40 * interest_score +
        0.20 * vibe_score +
        0.15 * lang_score +
        0.10 * age_fit +
        0.10 * look_score +
        0.05 * novelty
    )

    # Convert to 75% - 98% percentage range with small jitter
    jitter = random.uniform(-2, 2)
    percentage = int(min(max(total_score * 100 + jitter, 70), 98))
    return percentage
