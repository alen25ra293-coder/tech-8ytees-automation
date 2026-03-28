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

# ── 5 GENUINELY DIFFERENT script structures ───────────────────────────────────
# Each has a different opening move, different viewer psychology, different pacing.
SCRIPT_STRUCTURES = {

    "PRICE_SHOCK": {
        "description": "Open with the price gap. That IS the hook.",
        "template": (
            "HOOK (1 sentence, lead with price gap): [₹LOW vs ₹HIGH. One sentence, drop jaws immediately.]\n"
            "PROOF (2 sentences): [Specific feature or test result. Make it concrete — battery hours, speed, "
            "a measurement. Not vague praise.]\n"
            "TRUST (1 sentence): [Amazon reviews / sold count / how long you've used it.]\n"
            "SAVE CTA (1 sentence): [Save this. or Follow for daily finds like this.]"
        ),
        "example": (
            "₹499 versus ₹3,500. Same wireless charging speed — I timed it. "
            "This Portronics pad hits 15W, same as MagSafe, and I've used it daily for 4 months without issues. "
            "62,000 reviews on Amazon. Save this before you buy Apple's version."
        )
    },

    "FOUND_IT": {
        "description": "Discovery frame — you found something most people haven't.",
        "template": (
            "HOOK (1 sentence): [I found / Nobody told me / This exists — present tense discovery.]\n"
            "WHAT IT IS (1 sentence): [Product name, price, what it does.]\n"
            "WHY IT MATTERS (2 sentences): [Specific result or comparison. What does it replace? "
            "How much does that cost?]\n"
            "CTA (1 sentence): [Follow for more like this. or Save this before they raise the price.]"
        ),
        "example": (
            "Nobody told me this ₹799 plug existed. "
            "It's a Tapo P115 smart plug — tracks real-time power usage from your phone. "
            "I found my TV was wasting ₹300 a month on standby. Turned it off remotely, saved the money instantly. "
            "Follow for finds like this."
        )
    },

    "BEFORE_AFTER": {
        "description": "Problem first, product as the solution. Viewer sees themselves in the problem.",
        "template": (
            "PROBLEM HOOK (1 sentence): [Relatable frustration — spending too much, bad quality, "
            "common mistake people make.]\n"
            "THE SWITCH (1 sentence): [I switched to / I found / I tried — product name + price.]\n"
            "RESULT (2 sentences): [Specific measurable outcome. Numbers preferred. "
            "How long have you used it?]\n"
            "CTA (1 sentence): [Save this. or Follow to see what I test next.]"
        ),
        "example": (
            "I kept paying ₹5,000 for earbuds that died in a year. "
            "Switched to QCY T13s — ₹1,799. "
            "Six months later, zero issues, 30-hour battery, and noise cancelling my old ones didn't even have. "
            "I haven't touched the expensive ones since. Save this."
        )
    },

    "TEST_RESULT": {
        "description": "You ran a test. Results are the content. Data builds trust.",
        "template": (
            "SETUP (1 sentence): [I tested / I compared — product at ₹LOW vs ₹HIGH equivalent.]\n"
            "METHOD (1 sentence): [What specifically did you measure or do?]\n"
            "RESULT (2 sentences): [The actual number or outcome. Then the conclusion — "
            "which won and by how much?]\n"
            "CTA (1 sentence): [Save this. or Follow for more tests.]"
        ),
        "example": (
            "I timed a ₹499 wireless charger against a ₹3,500 MagSafe charging the same iPhone 13 from zero. "
            "Both started at the same time. "
            "₹499 charger finished 4 minutes faster. "
            "Same 15W chip, different logo, ₹3,000 difference. Save this."
        )
    },

    "DONT_BUY_YET": {
        "description": "Warning frame — stops scroll because viewer might be about to make a mistake.",
        "template": (
            "WARNING HOOK (1 sentence, under 6 words): [Don't buy [product] yet. Stop. Wait.]\n"
            "WHY (1 sentence): [The expensive version has a cheaper alternative that works just as well.]\n"
            "THE ALTERNATIVE (2 sentences): [Product name, exact price, key specs. "
            "One specific proof point — review count, test result, personal use.]\n"
            "CTA (1 sentence): [Save this before you order. or Follow for daily tech finds.]"
        ),
        "example": (
            "Don't buy AirPods yet. "
            "There's a ₹1,799 version that I genuinely cannot tell apart in a blind listen test. "
            "QCY T13 — noise cancelling, 30hr battery, 6 million sold worldwide. "
            "Save this before you spend ₹20,000."
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
9. LOOP TRICK: The last sentence should naturally connect back to the opening.
   Example: If you open with "₹499 vs ₹3,500" and end with "Save this" —
   change the ending to loop: "...and it starts at just ₹499."
   This makes viewers rewatch, boosting retention above 100%.

VISUAL INSTRUCTIONS — be VERY specific:
- Bad: "Show the product"
- Good: "[Close-up of hand holding ₹499 charger plugged into iPhone, charging
  indicator glowing green, MagSafe box visible in background with ₹3,499 tag]"
- FIRST VISUAL must be the "payoff" — the product in action, not a setup.

TITLE RULES:
- MAX 5 WORDS total. The core subject (e.g., "iPhone", "Jio") must be the 1st or 2nd word.
- USE NEGATIVE HOOKS: "Stop", "Don't Buy", "Warning", "Fake", "Dead?".
- exactly ONE high-contrast emoji at the very end (🛑, 💀, 🤯, 🚀).
- NO hashtags in title (they go in description only)
- NO sensational positive verbs (see banned list above)

PRODUCT_NAME RULE:
- Identify the specific brand and model from the topic (e.g., "Portronics PAT", "OnePlus 13", "Samsung Galaxy Buds").
- The product name MUST be mentioned explicitly in the SCRIPT — viewers need to know WHAT they're hearing about.
- Example: "This ₹499 Portronics charger..." or "OnePlus 13's camera..."

OUTPUT FORMAT (exact keys, no extra text):
PRODUCT_NAME: [specific brand and model name]
TITLE: [MAX 5 WORDS, NEGATIVE HOOK, 1 EMOJI AT END]
HOOK_LINE: [first sentence only, under 6 words, negative tone, NO banned verbs]
HOOK_STYLE: [{structure_name}]
SCRIPT: [50-65 words, INCLUDE PRODUCT NAME, follow the structure template above]
VISUAL_INSTRUCTIONS:
[Script line 1] -> Visual: [Specific Object + Action + Context]
[Script line 2] -> Visual: [Specific Object + Action + Context]
[continue for every line]
TAGS: [6 hashtags — 2 niche, 2 medium, 2 broad. No tags over 5M posts.]
DESCRIPTION: [1 curiosity-gap sentence that makes people click, NO boilerplate]
THUMBNAIL_TEXT: [2-3 words ALL CAPS — comparison or price gap]
CAPTION_HOOK: [1 punchy sentence for Instagram]
QUESTION: [1 controversial/opinionated question relevant to THIS specific product to drive comments]
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

    prompt = f"""Generate exactly 6 hashtags for a YouTube Shorts / Instagram Reels video about: "{topic}"

RULES:
- 2 NICHE (10k-100k posts): hyper-specific to the exact product or comparison
- 2 MEDIUM (100k-500k posts): category level  
- 2 BROAD (500k-2M posts): general tech/deals
- NEVER use tags with 5M+ posts (#Tech, #AI, #Viral, #Shorts — these bury content)
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
    words = [w.strip(".,!?$₹") for w in topic.split()[:3] if len(w) > 2]
    niche = " ".join(f"#{w.capitalize()}" for w in words if w)
    return f"{niche} #BudgetGadgets #CheapTechFinds #AmazonIndia #TechDeals #AffordableTech"


# ── Fallback script ───────────────────────────────────────────────────────────

def _build_fallback_script(topic: str) -> str:
    print("⚠️  Using fallback script.")
    safe = topic[:50]
    return f"""PRODUCT_NAME: Budget Tech Gadget
TITLE: {safe[:14].upper()} UNDER ₹2K
HOOK_LINE: Stop. Look at this.
HOOK_STYLE: DONT_BUY_YET
SCRIPT: Don't buy the expensive version yet. This gadget costs under ₹1,500 and I've used it for two months — it outperformed the ₹15,000 version every single time. 40,000 five-star reviews on Amazon. Save this.
VISUAL_INSTRUCTIONS:
[Don't buy the expensive version yet] -> Visual: [Expensive product with price tag, hand pushing it away]
[This gadget costs under ₹1,500] -> Visual: [Budget product unboxed, price visible on Amazon listing]
[outperformed the ₹15,000 version] -> Visual: [Side-by-side comparison, budget product highlighted as winner]
[40,000 five-star reviews] -> Visual: [Amazon page showing star rating and review count]
[Save this] -> Visual: [Text overlay SAVE THIS in yellow, product in background]
TAGS: #BudgetGadgets #CheapTech #AmazonIndia #HiddenGem #TechDeals #AffordableTech
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
        "thumbnail_text", "caption_hook", "question"
    ]
    data = {f: "" for f in fields}
    current_key = None
    buffer: list[str] = []

    for line in raw.strip().split("\n"):
        matched = False
        for key in fields:
            if line.upper().startswith(key.upper() + ":"):
                if current_key:
                    sep = "\n" if current_key == "visual_instructions" else " "
                    data[current_key] = sep.join(buffer).strip()
                current_key = key
                buffer = [line.split(":", 1)[-1].strip()]
                matched = True
                break
        if not matched and current_key:
            buffer.append(line.strip())

    if current_key:
        sep = "\n" if current_key == "visual_instructions" else " "
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
