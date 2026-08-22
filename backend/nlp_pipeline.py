"""
Multilingual intake -> structured request.

Two modes:
1. LLM mode (if ANTHROPIC_API_KEY is set): calls Claude with a structured
   prompt to translate + classify in one shot. This is the path you'd use
   in a real demo - swap in Bhashini's ASR/translation API upstream of this
   for voice input, this function only needs already-transcribed text.
2. Fallback mode (no API key): a rule-based keyword classifier so the whole
   pipeline runs end-to-end offline with zero setup. Good enough to prove
   the architecture without needing credentials during development.
"""
import os
import json
import re

USE_LLM = bool(os.getenv("ANTHROPIC_API_KEY"))

if USE_LLM:
    print("[nlp_pipeline] ANTHROPIC_API_KEY found - using Claude for translation/classification.")
else:
    print("[nlp_pipeline] No ANTHROPIC_API_KEY found - using offline keyword fallback.")

CATEGORY_KEYWORDS = {
    "road": ["road", "pothole", "highway", "bridge", "street", "sadak", "raste"],
    "water": ["water", "pipeline", "tap", "borewell", "drainage", "pani", "neeru"],
    "electricity": ["power", "electricity", "transformer", "outage", "bijli", "vidyuth"],
    "sanitation": ["garbage", "sewage", "toilet", "waste", "safai", "kasa"],
}

URGENCY_KEYWORDS = {
    "high": ["urgent", "emergency", "accident", "flood", "collapsed", "danger"],
    "medium": ["weeks", "worsening", "repeated"],
}


def _fallback_extract(text: str) -> dict:
    lower = text.lower()
    category = "other"
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            category = cat
            break

    urgency = "low"
    for level, kws in URGENCY_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            urgency = level
            break

    return {
        "translated_text": text,  # no-op translation in fallback mode
        "category": category,
        "urgency": urgency,
    }


def _llm_extract(text: str, language: str) -> dict:
    """
    Structured extraction via an LLM call. Kept isolated so it's easy to
    swap for a fine-tuned IndicBERT classifier later without touching
    callers of process_request().
    """
    import anthropic

    client = anthropic.Anthropic()
    prompt = f"""Translate the following citizen infrastructure complaint
(language code: {language}) into English, then classify it.

Text: "{text}"

Respond ONLY with JSON, no other text, in this exact shape:
{{"translated_text": "...", "category": "road|water|electricity|sanitation|other", "urgency": "low|medium|high"}}"""

    resp = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text
    raw = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)


def process_request(text: str, language: str = "en") -> dict:
    """Main entry point used by the API layer."""
    if USE_LLM:
        try:
            return _llm_extract(text, language)
        except Exception as e:
            # never let a flaky API call take down intake - degrade gracefully,
            # but print the reason so failures are visible during development
            print(f"[nlp_pipeline] LLM call failed ({e}) - falling back to keyword classifier.")
            return _fallback_extract(text)
    return _fallback_extract(text)
