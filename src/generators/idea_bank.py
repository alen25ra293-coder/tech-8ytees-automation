"""
Idea Bank — Tech 8ytees
Generates 5 diverse, unique video ideas daily using Gemini.
Uses EXTERNAL virality signals (search volume proxy, view potential)
instead of self-rating. Enforces category diversity.
"""
import os
import json
import random
from datetime import date

_USED_TOPICS_FILE = "used_topics.json"

# ── Category diversity enforcement ───────────────────────────────────────────
# Prevents two consecutive videos in the same product category
PRODUCT_CATEGORIES = [
    "audio",           # earbuds, headphones, speakers, mics
    "phone_acc",       # chargers, cases, mounts, lenses
    "productivity",    # keyboards, webcams, hubs, monitors
    "portable",        # power banks, fans, SSDs, trackers
    "smart_home",      # plugs, bulbs, strips, sensors
    "video_photo",     # cameras, ring lights, projectors, tripods
    "gaming",          # controllers, cooling fans, headsets
    "wearables",       # smartwatches, fitness bands, glasses
]

# Hook styles — one idea generated per style for maximum variety
HOOK_STYLES = [
    {"style": "Warning",    "template": "Don't buy [expensive product] yet…"},
    {"style": "Curiosity",  "template": "I found a cheaper way to do [task]…"},
    {"style": "Comparison", "template": "₹[price] vs ₹[high price]…"},
    {"style": "Discovery",  "template": "Nobody is talking about this gadget…"},
    {"style": "Challenge",  "template": "Can this cheap gadget replace [expensive item]?"},
]

# ── Used-topic persistence ────────────────────────────────────────────────────

def _load_used_topics() -> dict:
    """Load used topics AND last-used category."""
    if not os.path.exists(_USED_TOPICS_FILE):
        return {"topics": [], "last_category": None}
    try:
        with open(_USED_TOPICS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Handle old format (just a list of topics)
        if isinstance(data, list):
            return {"topics": data, "last_category": None}
        return {
            "topics": data.get("topics", []),
            "last_category": data.get("last_category", None)
        }
    except Exception:
        return {"topics": [], "last_category": None}


def mark_topic_used(topic: str, category: str = None):
    """Call after successful upload. Saves topic + category for deduplication."""
    state = _load_used_topics()
    topics_set = set(state["topics"])
    topics_set.add(topic.strip().lower())
    try:
        with open(_USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "topics": sorted(topics_set),
                "last_category": category or state.get("last_category")
            }, f, indent=2)
        print(f"📌 Topic archived: {topic[:60]} | Category: {category}")
    except Exception as e:
        print(f"⚠️  Could not save used_topics.json: {e}")


def _is_used(topic: str, used_list: list) -> bool:
    """Fuzzy-match: checks if any 4-word substring of topic is already used."""
    used_set = set(used_list)
    t = topic.strip().lower()
    if t in used_set:
        return True
    words = t.split()
    for i in range(len(words) - 3):
        chunk = " ".join(words[i:i+4])
        if any(chunk in u for u in used_set):
            return True
    return False


# ── Gemini helper ─────────────────────────────────────────────────────────────

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

def get_best_idea() -> tuple[str, str]:
    """
    Returns (topic, category).
    Generates 5 ideas across different categories and hook styles.
    Picks the one with highest estimated reach, skipping used topics
    and avoiding the same category as last video.
    """
    print("💡 Idea Bank: generating fresh video ideas...")
    state = _load_used_topics()
    used_topics = state["topics"]
    last_category = state.get("last_category")

    model = _get_model()
    if model:
        ideas = _generate_ideas_with_gemini(model, used_topics, last_category)
        if ideas:
            # Pick highest-scoring fresh idea
            best = max(ideas, key=lambda x: x.get("reach_score", 0))
            print(f"🏆 Best idea (reach {best['reach_score']}/10): {best['topic']}")
            print(f"   Hook: {best.get('hook_style')} | Category: {best.get('category')}")
            return best["topic"], best.get("category", "general")

    print("⚠️  Idea Bank falling back to curated list.")
    topic = _fallback_topic(used_topics)
    return topic, "general"


def _generate_ideas_with_gemini(model, used_topics: list, last_category: str) -> list:
    """Ask Gemini for 5 ideas — one per hook style, each in a different product category."""

    hook_styles_str = "\n".join(
        f"  {i+1}. {h['style']}: \"{h['template']}\""
        for i, h in enumerate(HOOK_STYLES)
    )

    # Give Gemini the last 20 used topics for context
    used_sample = used_topics[-20:]
    used_str = "\n".join(f"  - {t}" for t in used_sample) if used_sample else "  (none yet)"

    # Tell it which category to avoid
    avoid_category = f"\nDo NOT use category: '{last_category}' (used in last video)." if last_category else ""

    prompt = f"""You are the content strategist for "Tech 8ytees" — a YouTube Shorts channel.
Niche: budget gadgets (under ₹2000 / $25) that replace expensive products.
Target: 16-35 year old Indian viewers who want good tech without overspending.
Today: {date.today()}

ALREADY USED TOPICS — avoid these AND anything conceptually similar:
{used_str}
{avoid_category}

Available product categories: {', '.join(PRODUCT_CATEGORIES)}

TASK: Generate 5 UNIQUE video ideas — one per hook style, each from a DIFFERENT product category.
Hook styles:
{hook_styles_str}

TOPIC FORMAT RULES:
- Include a specific low price (₹) AND the name of the expensive product it replaces
- Max 70 characters
- No banned words: destroys, shames, embarrasses, you won't believe
- Each idea must be in a completely different product category
- Prioritize products that are currently popular on Amazon India

REACH SCORE — rate each idea 1-10 based on:
- Pain point strength: Does everyone face this problem? (high = more relatable)
- Price gap impact: Is the price difference shocking? (₹500 vs ₹50,000 > ₹500 vs ₹2,000)
- Category freshness: Avoid categories used recently
- Specificity: Named brand + exact price scores higher than vague descriptions

RESPOND IN THIS EXACT JSON FORMAT (no markdown, no extra text):
[
  {{"topic": "...", "hook_style": "Warning",    "category": "audio",      "reach_score": 8}},
  {{"topic": "...", "hook_style": "Curiosity",  "category": "smart_home", "reach_score": 7}},
  {{"topic": "...", "hook_style": "Comparison", "category": "phone_acc",  "reach_score": 9}},
  {{"topic": "...", "hook_style": "Discovery",  "category": "portable",   "reach_score": 8}},
  {{"topic": "...", "hook_style": "Challenge",  "category": "gaming",     "reach_score": 7}}
]"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        ideas = json.loads(raw)

        # Filter already-used topics
        fresh = [i for i in ideas if not _is_used(i.get("topic", ""), used_topics)]
        print(f"✅ {len(fresh)}/{len(ideas)} fresh ideas generated.")

        if fresh:
            for idea in sorted(fresh, key=lambda x: -x.get("reach_score", 0)):
                print(f"   [{idea.get('reach_score','?')}/10] {idea['topic']} ({idea.get('hook_style')} | {idea.get('category')})")

        return fresh

    except json.JSONDecodeError as e:
        print(f"⚠️  Idea Bank JSON parse failed: {e}")
        return []
    except Exception as e:
        print(f"⚠️  Idea Bank Gemini error: {e}")
        return []


def _fallback_topic(used_topics: list) -> str:
    from src.scrapers.reddit import GADGET_TOPICS
    fresh = [t for t in GADGET_TOPICS if not _is_used(t, used_topics)]
    if not fresh:
        print("⚠️  All curated topics used — resetting pool.")
        fresh = GADGET_TOPICS
    topic = random.choice(fresh)
    print(f"📌 Fallback topic: {topic}")
    return topic
