"""
Idea Bank — Tech 8ytees
Generates 5 diverse, unique video ideas daily using Gemini.
Self-rates each idea for virality (1–10) and returns the top scorer.
Persists used_topics.json to prevent topic repetition across days.
"""
import os
import json
import random
from datetime import date

# ── Paths ─────────────────────────────────────────────────────────────────────
_USED_TOPICS_FILE = "used_topics.json"


# ── Hook style templates ──────────────────────────────────────────────────────
HOOK_STYLES = [
    {"style": "Warning",     "template": "Don't buy [expensive product] yet…"},
    {"style": "Curiosity",   "template": "I found a cheaper way to do [task]…"},
    {"style": "Comparison",  "template": "₹[price] vs ₹[high price]…"},
    {"style": "Discovery",   "template": "Nobody is talking about this gadget…"},
    {"style": "Challenge",   "template": "Can this cheap gadget replace [expensive item]?"},
]


# ── Used-topic persistence ────────────────────────────────────────────────────

def _load_used_topics() -> set:
    if not os.path.exists(_USED_TOPICS_FILE):
        return set()
    try:
        with open(_USED_TOPICS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("topics", []))
    except Exception:
        return set()


def mark_topic_used(topic: str):
    """Call this after a successful video upload to prevent future repetition."""
    used = _load_used_topics()
    used.add(topic.strip().lower())
    try:
        with open(_USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump({"topics": sorted(used)}, f, indent=2)
        print(f"📌 Topic marked used: {topic[:60]}")
    except Exception as e:
        print(f"⚠️  Could not save used_topics.json: {e}")


def _is_used(topic: str, used: set) -> bool:
    """Fuzzy-match: checks if any 4-word substring of topic is already used."""
    t = topic.strip().lower()
    if t in used:
        return True
    words = t.split()
    for i in range(len(words) - 3):
        chunk = " ".join(words[i:i+4])
        if any(chunk in u for u in used):
            return True
    return False


# ── Gemini helpers ─────────────────────────────────────────────────────────────

def _get_model():
    try:
        import google.generativeai as genai
        keys_raw = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
        keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
        if not keys:
            return None
        genai.configure(api_key=random.choice(keys))
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        return None


# ── Main entrypoint ───────────────────────────────────────────────────────────

def get_best_idea() -> str:
    """
    Generate 5 diverse video ideas (one per hook style), rate each for virality,
    skip already-used topics, and return the highest-scoring fresh idea.
    Falls back to the curated topic list if Gemini is unavailable.
    """
    print("💡 Idea Bank: generating fresh video ideas...")
    used = _load_used_topics()
    model = _get_model()

    if model:
        ideas = _generate_ideas_with_gemini(model, used)
        if ideas:
            best = max(ideas, key=lambda x: x.get("virality_score", 0))
            print(f"🏆 Best idea (score {best['virality_score']}/10): {best['topic']}")
            print(f"   Hook style: {best.get('hook_style', 'unknown')}")
            return best["topic"]

    # Fallback: curated list with deduplication
    print("⚠️  Idea Bank falling back to curated topic list.")
    return _fallback_topic(used)


def _generate_ideas_with_gemini(model, used: set) -> list:
    """Ask Gemini to generate 5 ideas with virality scores."""
    hook_styles_str = "\n".join(
        f"  {i+1}. {h['style']}: \"{h['template']}\""
        for i, h in enumerate(HOOK_STYLES)
    )
    used_sample = list(used)[-20:]  # last 20 used topics for context
    used_str = "\n".join(f"  - {t}" for t in used_sample) if used_sample else "  (none yet)"

    prompt = f"""You are the content strategist for "Tech 8ytees" — a viral YouTube Shorts channel.
Niche: cheap gadgets (under ₹2000 / $25) that replace expensive products
Target: 16-35 Indian tech-curious viewers who love saving money
Today's date: {date.today()}

ALREADY USED TOPICS (avoid these or anything too similar):
{used_str}

TASK: Generate exactly 5 UNIQUE video ideas — one for each hook style:
{hook_styles_str}

VIDEO TOPIC FORMAT:
- Include a specific low price (₹ or $) AND the expensive product it replaces
- Max 70 characters
- No banned words: no "destroys", "shames", "embarrasses", "you won't believe"
- Each idea must feel completely different from the others

For each idea, rate its virality from 1–10 based on:
- Specificity (named product + exact price = higher score)
- Curiosity gap
- Relatable pain point
- Freshness (not overused topic)

RESPOND IN THIS EXACT JSON FORMAT (no markdown, no extra text):
[
  {{"topic": "...", "hook_style": "Warning", "virality_score": 8}},
  {{"topic": "...", "hook_style": "Curiosity", "virality_score": 7}},
  {{"topic": "...", "hook_style": "Comparison", "virality_score": 9}},
  {{"topic": "...", "hook_style": "Discovery", "virality_score": 8}},
  {{"topic": "...", "hook_style": "Challenge", "virality_score": 7}}
]"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        ideas = json.loads(raw)

        # Filter out already-used topics
        fresh = [i for i in ideas if not _is_used(i.get("topic", ""), used)]
        print(f"✅ Idea Bank: {len(fresh)}/{len(ideas)} fresh ideas generated.")

        if fresh:
            for idea in sorted(fresh, key=lambda x: -x.get("virality_score", 0)):
                print(f"   [{idea.get('virality_score', '?')}/10] {idea['topic']} ({idea.get('hook_style','')})")
        return fresh

    except json.JSONDecodeError as e:
        print(f"⚠️  Idea Bank JSON parse failed: {e}")
        return []
    except Exception as e:
        print(f"⚠️  Idea Bank Gemini error: {e}")
        return []


def _fallback_topic(used: set) -> str:
    """Pick a fresh topic from the curated list, avoiding already-used ones."""
    # Import inline to avoid circular imports
    from src.scrapers.reddit import GADGET_TOPICS
    fresh = [t for t in GADGET_TOPICS if not _is_used(t, used)]
    if not fresh:
        print("⚠️  All curated topics used — resetting pool.")
        fresh = GADGET_TOPICS
    topic = random.choice(fresh)
    print(f"📌 Fallback topic: {topic}")
    return topic
