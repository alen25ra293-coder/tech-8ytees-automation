"""
Script Generator — Tech 8ytees
Viral 23-26 second scripts optimized for retention.
Niche: Budget gadgets under ₹2000 / $25 replacing expensive products.

KEY CHANGES FROM V1:
- 5 genuinely different script STRUCTURES (not just hook styles)
- Branded intro REMOVED — wastes 15% of video
- Hook must pay off in first 4 words, not set up
- Conversational language, not marketing copy
- Self-rating removed — it was fake signal
"""
import os
import random
from datetime import date

# ── API key rotation ──────────────────────────────────────────────────────────
_gemini_keys_raw = (
    os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
)
GEMINI_KEYS = [k.strip() for k in _gemini_keys_raw.split(",") if k.strip()]
_key_index = 0

# ── Clickbait words YouTube suppresses (kills impressions) ─────────────────────
BANNED_WORDS = [
    # Sensational verbs YouTube demotes
    "destroys", "shames", "embarrasses", "outsmarts", "shocks",
    "kills", "crushes", "slays", "wrecks", "humiliates",
    "obliterates", "annihilates", "demolishes", "exposes",
    # Clickbait phrases
    "won't believe", "will blow your mind", "you need to see",
    "mind-blowing", "insane", "unbelievable", "jaw-dropping",
    # Branded intros (waste 15% of video)
    "welcome back", "welcome to", "tech 8ytees", "hey guys",
]


def _next_key():
    global _key_index
    if not GEMINI_KEYS:
        return None
    key = GEMINI_KEYS[_key_index]
    _key_index = (_key_index + 1) % len(GEMINI_KEYS)
    return key


def _get_model():
    try:
        import google.generativeai as genai
    except ImportError:
        return None
    key = _next_key()
    if not key:
        return None
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-2.5-flash")


NICHE = "budget gadgets under ₹2000 / $25 that replace expensive products"
TARGET_AUDIENCE = "16-35 year old Indians who want good tech without overspending"

# ── 6 GENUINELY DIFFERENT script structures ───────────────────────────────────
# Each has a different opening move, different viewer psychology, different pacing.
SCRIPT_STRUCTURES = {

    "STORY_REGRET": {
        "description": "Start with a painful personal mistake (spending too much). High empathy.",
        "template": (
            "HOOK (1 sentence): [I wasted ₹[High Amount] on [Expensive Brand] so you don't have to.]\n"
            "THE SWITCH (1 sentence): [Instead, I daily-drove this [Price] [Product Name] for 30 days.]\n"
            "THE REVEAL (2 sentences): [Specific feature comparison. E.g., 'The battery lasted 4 days longer' or 'The build quality is identical metal'.]\n"
            "LOOP_OUT (1 sentence): [A setup sentence that leads back to the HOOK. e.g., 'I honestly can't believe...']"
        ),
        "example": (
            "I wasted ₹25,000 on AirPods Pro so you don't have to. "
            "Instead, I daily-drove these ₹1,799 QCY earbuds for a whole month. "
            "The active noise cancellation is identical in traffic, and the battery actually lasts two days longer. "
            "It's painful because I honestly can't believe..."
        )
    },

    "SECRET_DISCOVERY": {
        "description": "The 'Tech reviewers are gatekeeping this' angle. Very high curiosity.",
        "template": (
            "HOOK (1 sentence): [Tech reviewers are completely ignoring this ₹[Price] [Gadget Category].]\n"
            "WHAT IT IS (1 sentence): [It's the [Product Name] and it literally replaces [Expensive Tool].]\n"
            "PROOF (2 sentences): [Specific result. How does it make life easier? Name a concrete spec.]\n"
            "LOOP_OUT (1 sentence): [Leads back to the hook. e.g., 'And that's exactly why...']"
        ),
        "example": (
            "Tech reviewers are completely ignoring this ₹799 smart plug. "
            "It's the Tapo P115 and it literally replaces a ₹4,000 energy monitor. "
            "I plugged my old AC into it and found out it was draining ₹500 a month in standby power alone. "
            "And that's exactly why..."
        )
    },

    "LONG_TERM_TEST": {
        "description": "Builds ultimate trust by claiming long-term usage.",
        "template": (
            "HOOK (1 sentence): [I've used the [Product Name] every single day for 6 months.]\n"
            "THE VERDICT (1 sentence): [And it completely ruined my [Expensive Brand Product] for me.]\n"
            "DETAILS (2 sentences): [Why? Specific spec comparison — weight, speed, durability. Mention the price gap here.]\n"
            "LOOP_OUT (1 sentence): [Leads back to hook.]"
        ),
        "example": (
            "I've used this Portronics MagSafe charger every single day for 6 months. "
            "And it completely ruined my Apple charger for me. "
            "It hits the exact same 15W charging speed, but it costs ₹499 instead of ₹3,500. "
            "Honestly, I've used..."
        )
    },

    "PAIN_POINT": {
        "description": "Start with a highly relatable daily annoyance.",
        "template": (
            "HOOK (1 sentence): [If you hate [Specific Daily Tech Annoyance], you need to see this.]\n"
            "THE FIX (1 sentence): [This is the ₹[Price] [Product Name].]\n"
            "RESULT (2 sentences): [How it perfectly solves the annoyance. Concrete details.]\n"
            "LOOP_OUT (1 sentence): [Leads back to hook.]"
        ),
        "example": (
            "If you hate your phone dying at 2 PM, you need to see this. "
            "This is the ₹999 Ambrane 10000mAh mini power bank. "
            "It's the size of a credit card, snaps right to the back of your phone, and charges it to 100% in 45 minutes. "
            "Seriously, if you hate..."
        )
    }
}

_LAST_STRUCTURE = None


def _pick_structure() -> tuple[str, dict]:
    """Pick a script structure, avoiding repeating the same one twice in a row."""
    global _LAST_STRUCTURE
    keys = list(SCRIPT_STRUCTURES.keys())
    if _LAST_STRUCTURE:
        keys = [k for k in keys if k != _LAST_STRUCTURE] or keys
    name = random.choice(keys)
    _LAST_STRUCTURE = name
    return name, SCRIPT_STRUCTURES[name]


# ── Main script generation ────────────────────────────────────────────────────

def generate_script(topic: str, attempt: int = 1) -> str | None:
    """Generate a viral 50-70 word script for a 23-26 second video."""
    print(f"🤖 Generating script (attempt {attempt}/3)...")

    structure_name, structure = _pick_structure()
    print(f"   Structure: {structure_name} — {structure['description']}")

    model = _get_model()
    if not model:
        print("❌ No Gemini keys. Using fallback.")
        return _build_fallback_script(topic)

    prompt = f"""You are the scriptwriter for "Tech 8ytees" — a YouTube Shorts channel.
Niche: {NICHE}
Audience: {TARGET_AUDIENCE}
Today: {date.today()}

YOU ARE WRITING A 23-26 SECOND VIDEO SCRIPT. The algorithm judges retention from the FIRST FRAME (0-400ms).

═══════════════════════════════════════════════════
TOPIC: "{topic}"
SCRIPT STRUCTURE TO USE: {structure_name}
STRUCTURE DESCRIPTION: {structure['description']}

TEMPLATE:
{structure['template']}

EXAMPLE OF THIS STRUCTURE:
{structure['example']}
═══════════════════════════════════════════════════

ABSOLUTE RULES:
1. NO branded intro. First word must be a hook — not a greeting.
2. MAX 65 WORDS total. Count every word. Cut ruthlessly.
3. Sound like a real person talking to a friend — not marketing copy.
4. Prices in ₹ (Indian Rupees).
5. NEVER use sensational/clickbait verbs. BANNED: destroys, shames, embarrasses,
   outsmarts, shocks, kills, crushes, slays, wrecks, humiliates, obliterates,
   annihilates, demolishes, exposes, mind-blowing, insane, unbelievable, jaw-dropping.
   Instead use SPECIFIC COMPARISONS: "same 15W speed", "4 minutes faster",
   "identical sound quality in blind test".
6. Every script line needs a matching visual instruction.
7. DEMO visuals must show a clear before/after or split-screen result.
8. FIRST FRAME RULE: The very first visual MUST show the product result/payoff
   immediately — a glowing screen, a side-by-side price comparison, hands holding
   the product. NOT a setup, NOT text, NOT a black screen.
9. LOOP TRICK: The last sentence should naturally connect back to the opening but before looping, you MUST include the engagement hack exactly:
   "Check the first comment for the link! [Controversial Question e.g. Android or iPhone]? Comment below!"
   End the script with this CTA.
   This makes viewers rewatch and signals high engagement to the algorithm.

VISUAL INSTRUCTIONS — be VERY specific:
- Bad: "Show the product"
- Good: "[Close-up of hand holding ₹499 charger plugged into iPhone, charging
  indicator glowing green, MagSafe box visible in background with ₹3,499 tag]"
- FIRST VISUAL must be the "payoff" — the product in action, not a setup.

PRODUCT_NAME RULE (CRITICAL):
- Identify the specific brand and model from the topic (e.g., "Portronics PAT", "OnePlus 13", "Samsung Galaxy Buds").
- The SCRIPT body MUST mention the product name IN THE FIRST OR SECOND SENTENCE.
- DO NOT say "this gadget" or "this device" — SAY THE ACTUAL PRODUCT NAME.

SEAMLESS LOOP RULE (CRITICAL):
- The last sentence of the script (LOOP_OUT) MUST end in a way that leads perfectly back to the first word of the hook.
- Example: 
  Hook: "₹499 versus ₹3,500..." 
  Loop_out: "...so stop overpaying for brands just for"
  Result: When the video ends, it loops back to "₹499 vs ₹3,500..." seamlessly.

OUTPUT FORMAT (exact keys, no extra text):
PRODUCT_NAME: [specific brand and model name]
TITLE: [UNDER 60 CHARS, FOCUS ON MONEY SAVED OR PROBLEM SOLVED, 1 EMOJI AT END]
HOOK_LINE: [first sentence only, under 6 words]
HOOK_STYLE: [{structure_name}]
SCRIPT: [50-65 words, SEAMLESS LOOP REQUIRED, mention product name in first 2 sentences]
VISUAL_INSTRUCTIONS:
[Script line 1] -> Visual: [Specific Object + Action + Context]
[Script line 2] -> Visual: [Specific Object + Action + Context]
[continue for every line]
TAGS: [Exactly 3 hashtags chosen ONLY from this list: #tech, #techessentials, #budgettech, #smartgadgets, #techreview. NO OTHER TAGS ALLOWED.]
DESCRIPTION: [Generate a FULL YouTube description for this specific video.]
THUMBNAIL_TEXT: [2-3 words ALL CAPS]
CAPTION_HOOK: [1 punchy sentence for Instagram]
PINNED_COMMENT: [Engagement question for comments]
QUESTION: [Controversial/opinionated question relevant to THIS specific product]
"""

    try:
        response = model.generate_content(prompt)
        script_text = response.text.strip()

        # Word count check
        if "SCRIPT:" in script_text:
            body = script_text.split("SCRIPT:")[1]
            for end_key in ["VISUAL_INSTRUCTIONS:", "TAGS:", "DESCRIPTION:"]:
                if end_key in body:
                    body = body.split(end_key)[0]
                    break
            wc = len(body.strip().split())
            print(f"📝 Script: {wc} words")
            if wc < 40 or wc > 75:
                if attempt < 3:
                    print(f"⚠️  Out of range ({wc}w). Regenerating...")
                    return generate_script(topic, attempt + 1)
                print("⚠️  Accepting despite length — 3 attempts exhausted.")

        # Banned word check
        raw_lower = script_text.lower()
        found_banned = [bw for bw in BANNED_WORDS if bw in raw_lower]
        if found_banned:
            if attempt < 3:
                print(f"⚠️  Banned words: {found_banned}. Regenerating...")
                return generate_script(topic, attempt + 1)
            print(f"⚠️  Banned words remain after 3 attempts: {found_banned}")

        # Product name validation
        if "PRODUCT_NAME:" in script_text and "SCRIPT:" in script_text:
            product_line = script_text.split("PRODUCT_NAME:")[1].split("\n")[0].strip()
            script_body = script_text.split("SCRIPT:")[1]
            for end_key in ["VISUAL_INSTRUCTIONS:", "TAGS:", "DESCRIPTION:"]:
                if end_key in script_body:
                    script_body = script_body.split(end_key)[0]
                    break
            
            # Check if product name contains actual brand (not generic)
            generic_terms = ["budget tech gadget", "budget gadget", "tech gadget", "gadget", "device", "product"]
            is_generic = any(term in product_line.lower() for term in generic_terms)
            
            # Extract brand name (first word of product name, usually the brand)
            brand_words = [w for w in product_line.split() if len(w) > 2 and w.lower() not in ["the", "this", "and"]]
            
            if is_generic or not brand_words:
                if attempt < 3:
                    print(f"⚠️  Generic product name '{product_line}'. Regenerating...")
                    return generate_script(topic, attempt + 1)
                print(f"⚠️  Product name is generic: '{product_line}'")
            elif brand_words and not any(word.lower() in script_body.lower() for word in brand_words[:2]):
                if attempt < 3:
                    print(f"⚠️  Product name '{product_line}' not in script. Regenerating...")
                    return generate_script(topic, attempt + 1)
                print(f"⚠️  Product '{product_line}' not mentioned in script body")

        return script_text

    except Exception as e:
        err = str(e).lower()
        if ("quota" in err or "resource_exhausted" in err) and attempt <= len(GEMINI_KEYS):
            return generate_script(topic, attempt + 1)
        print(f"❌ Gemini error: {e}")
        return _build_fallback_script(topic)


# ── Dynamic hashtag generation ────────────────────────────────────────────────

def generate_dynamic_hashtags(topic: str) -> str:
    """2 niche + 2 medium + 2 broad hashtags. Never over 5M posts."""
    print("🏷️  Generating hashtags...")
    model = _get_model()
    if not model:
        return _fallback_hashtags(topic)

    prompt = f"""Generate exactly 3 hashtags for a YouTube Shorts / Instagram Reels video about: "{topic}"

RULES:
- Select exactly 3 tags from this approved list ONLY: #tech, #techessentials, #budgettech, #smartgadgets, #techreview.
- Under no circumstances should you generate tags outside of this list.
- Output ONLY hashtags separated by spaces. No other text."""

    try:
        resp = model.generate_content(prompt)
        tags = resp.text.strip()
        if "#" in tags and len(tags) > 10:
            print(f"✅ Hashtags: {tags}")
            return tags
    except Exception:
        pass
    return _fallback_hashtags(topic)


def _fallback_hashtags(topic: str) -> str:
    return "#tech #budgettech #smartgadgets"


# ── Fallback script ───────────────────────────────────────────────────────────

def _build_fallback_script(topic: str) -> str:
    print("⚠️  Using fallback script.")
    safe = topic[:50]
    return f"""PRODUCT_NAME: Budget Tech Gadget
TITLE: This ₹1,500 Gadget Beats The ₹15,000 Version 🛑
HOOK_LINE: Don't buy the expensive version yet.
HOOK_STYLE: DONT_BUY_YET
SCRIPT: Don't buy the expensive version yet. This gadget costs under ₹1,500 and I've used it for two months — it outperformed the ₹15,000 version every single time. 40,000 five-star reviews on Amazon. Save this.
VISUAL_INSTRUCTIONS:
[Don't buy the expensive version yet] -> Visual: [Expensive product with price tag, hand pushing it away]
[This gadget costs under ₹1,500] -> Visual: [Budget product unboxed, price visible on Amazon listing]
[outperformed the ₹15,000 version] -> Visual: [Side-by-side comparison, budget product highlighted as winner]
[40,000 five-star reviews] -> Visual: [Amazon page showing star rating and review count]
[Save this] -> Visual: [Text overlay SAVE THIS in yellow, product in background]
TAGS: #tech #budgettech #smartgadgets
DESCRIPTION: This gadget costs 10x less and somehow does the job better
THUMBNAIL_TEXT: BUDGET WINS
CAPTION_HOOK: This ₹1,500 gadget made my ₹15,000 one obsolete 👀
QUESTION: What overpriced gadget should I test next?"""


# ── Script parsing ────────────────────────────────────────────────────────────

def parse_script(raw: str) -> dict | None:
    if not raw:
        return None

    fields = [
        "product_name", "title", "hook_line", "hook_style", "script",
        "visual_instructions", "tags", "description",
        "thumbnail_text", "caption_hook", "pinned_comment", "question"
    ]
    data = {f: "" for f in fields}
    current_key = None
    buffer: list[str] = []

    for line in raw.strip().split("\n"):
        matched = False
        for key in fields:
            if line.upper().startswith(key.upper() + ":"):
                if current_key:
                    sep = "\n" if current_key in ("visual_instructions", "description", "pinned_comment") else " "
                    data[current_key] = sep.join(buffer).strip()
                current_key = key
                buffer = [line.split(":", 1)[-1].strip()]
                matched = True
                break
        if not matched and current_key:
            buffer.append(line.strip())

    if current_key:
        sep = "\n" if current_key in ("visual_instructions", "description", "pinned_comment") else " "
        data[current_key] = sep.join(buffer).strip()

    # ── Fallbacks ─────────────────────────────────────────────────────────────
    if not data["thumbnail_text"] and data["title"]:
        data["thumbnail_text"] = " ".join(data["title"].split()[:3]).upper()

    if not data["caption_hook"] and data["title"]:
        data["caption_hook"] = "This budget gadget just beat something 10x its price 👀"

    if not data["question"]:
        data["question"] = "What overpriced gadget should I test next?"

    if not data["visual_instructions"]:
        data["visual_instructions"] = (
            "FIRST FRAME: Hand holding product with price visible | "
            "PROBLEM: Split-screen showing expensive alternative with price | "
            "SOLUTION: Budget product specs close-up | DEMO: Side-by-side comparison | "
            "PAYOFF: Text overlay with both prices"
        )

    # ── Strip hashtags from title (they belong in description only) ───────────
    import re as _re
    if data["title"]:
        data["title"] = _re.sub(r'#\w+', '', data["title"]).strip()
        # Clean up any double spaces left behind
        data["title"] = _re.sub(r'\s{2,}', ' ', data["title"]).strip()

    # ── Auto-append subscribe CTA if missing ─────────────────────────────────
    subscribe_ctas = ["subscribe", "sub for", "follow for more", "follow for daily",
                      "save this", "follow to see"]
    if data["script"] and not any(c in data["script"].lower() for c in subscribe_ctas):
        data["script"] = data["script"].rstrip() + " Subscribe for daily finds like this."
        print("ℹ️  Subscribe CTA auto-appended.")

    # ── Banned word check on TITLE, HOOK, and SCRIPT ─────────────────────────
    for field_name in ["title", "hook_line", "script"]:
        field_text = data.get(field_name, "").lower()
        found_banned = [bw for bw in BANNED_WORDS if bw in field_text]
        if found_banned:
            print(f"⚠️  Banned words in {field_name}: {found_banned}")
            # Auto-replace banned words in title and hook_line
            if field_name in ("title", "hook_line"):
                for bw in found_banned:
                    # Replace with neutral alternatives
                    replacements = {
                        "destroys": "vs", "shames": "vs", "embarrasses": "vs",
                        "outsmarts": "vs", "shocks": "vs", "kills": "vs",
                        "crushes": "vs", "slays": "vs", "wrecks": "vs",
                        "humiliates": "vs", "obliterates": "vs",
                        "annihilates": "vs", "demolishes": "vs", "exposes": "vs",
                    }
                    replacement = replacements.get(bw, "vs")
                    data[field_name] = _re.sub(
                        bw, replacement, data[field_name], flags=_re.IGNORECASE
                    )
                print(f"   🔧 Auto-fixed {field_name}: \"{data[field_name]}\"")

    wc = len(data["script"].split())
    print(f'✅ Script parsed — "{data["title"]}" ({wc} words) | Structure: {data.get("hook_style","?")}')
    return data
