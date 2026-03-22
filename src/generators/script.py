"""
Script Generator — Tech 8ytees
Viral 23-26 second scripts optimized for <20% skip rate.
Niche: Budget gadgets and hidden tech gems under $50 that most people don't know about.
"""
import os
import random
from datetime import date
import google.generativeai as genai

# ── API key rotation ─────────────────────────────────────────────────────────
_gemini_keys_raw = (
    os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
)
GEMINI_KEYS = [k.strip() for k in _gemini_keys_raw.split(",") if k.strip()]
_key_index = 0


def _next_key():
    global _key_index
    if not GEMINI_KEYS:
        return None
    key = GEMINI_KEYS[_key_index]
    _key_index = (_key_index + 1) % len(GEMINI_KEYS)
    return key


def _get_model():
    key = _next_key()
    if not key:
        return None
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-2.5-flash")


# ── Niche constants ──────────────────────────────────────────────────────────
NICHE = "budget gadgets and hidden tech gems under $50 that most people don't know about"
HOOK_FORMULA = 'This $[price] [product] does what your $[expensive product] can\'t'
TARGET_AUDIENCE = "people who want the best tech without spending a lot of money"

# ── Niche-specific topics ────────────────────────────────────────────────────
NICHE_TOPICS = [
    "$15 Bluetooth speaker that sounds like a $300 JBL",
    "$20 phone camera lens that replaces $800 DSLR shots",
    "$12 wireless charger that beats $50 Apple MagSafe",
    "$25 mini projector that replaces your bedroom TV",
    "$18 magnetic phone mount that beats any car mount",
    "$10 USB-C hub that does what a $100 docking station does",
    "$22 noise-cancelling earbuds that rival $250 AirPods Pro",
    "$30 ring light that makes you look like a studio setup",
    "$8 cable organizer that fixes your messy desk forever",
    "$15 portable monitor that turns your phone into a laptop",
    "$28 smart plug that cuts your electricity bill in half",
    "$35 keyboard that types better than a $200 mechanical",
    "$20 desk lamp with wireless charging nobody knows about",
    "$12 action camera that shoots like a $400 GoPro",
    "$14 selfie stick tripod that every creator needs",
    "$25 trackpad for Windows that feels like a MacBook",
    "$18 LED strip lights that transform any room",
    "$30 power bank that charges 3 devices at once",
    "$15 Smart TV remote that controls everything",
    "$22 webcam that beats $100+ Logitech models",
    "$20 typeC headphone adapter with built-in DAC",
    "$35 handheld fan that's basically portable AC",
    "$10 screen cleaner kit that brings old screens back to life",
    "$28 portable SSD that's faster than most laptop drives",
]

# ── Series content rotation (Sat-Mon, Tue-Wed, Thu-Fri) ──────────────────────
SERIES_THEMES = {
    5: {"name": "Hidden Gem", "hashtag": "#HiddenGem"},              # Saturday
    6: {"name": "Hidden Gem", "hashtag": "#HiddenGem"},              # Sunday
    0: {"name": "Hidden Gem", "hashtag": "#HiddenGem"},              # Monday
    1: {"name": "Cheap vs Expensive", "hashtag": "#CheapVsExpensive"},  # Tuesday
    2: {"name": "Cheap vs Expensive", "hashtag": "#CheapVsExpensive"},  # Wednesday
    3: {"name": "Gadget That Changed Everything", "hashtag": "#GadgetGameChanger"},  # Thursday
    4: {"name": "Gadget That Changed Everything", "hashtag": "#GadgetGameChanger"},  # Friday
}


def get_series_theme():
    """Get today's series theme based on day of week."""
    weekday = date.today().weekday()
    theme = SERIES_THEMES.get(weekday)
    if theme:
        print(f"📅 Series: {theme['name']} ({theme['hashtag']})")
    return theme


# ── Few-shot examples — 60-75 words, punchy ─────────────────────────────────
EXAMPLE_SCRIPTS = [
    {
        "topic": "$22 earbuds that rival $250 AirPods Pro",
        "title": "These $22 Earbuds DESTROYED My AirPods",
        "script": (
            "Throw your AirPods away. These 22 dollar earbuds have noise cancelling, "
            "30 hour battery, and sound quality that makes 250 dollar AirPods feel like "
            "a scam. They're called QCY T13. Six million sold. I tested them for 3 months "
            "and I haven't touched my AirPods since. Apple charges you 250 bucks for a "
            "brand name. Stop falling for it. "
            "Save this before you buy your next gadget. "
            "What gadget should I test next? Comment below."
        ),
    },
    {
        "topic": "$12 action camera that shoots like a $400 GoPro",
        "title": "This $12 Camera EMBARRASSES GoPro",
        "script": (
            "Stop buying GoPros. This 12 dollar action camera shoots in 4K, "
            "is waterproof, and fits in your pocket. It's on Amazon with 50,000 reviews. "
            "I took it surfing, hiking, and biking. The footage? People thought it was a "
            "GoPro Hero 12. That costs 400 dollars. This costs 12. Same shots. "
            "Your expensive camera is a waste of money. "
            "Save this before you buy your next gadget. "
            "Which overpriced gadget should I expose next? Comment below."
        ),
    },
]

# -- Pattern-interrupt hooks (under 5 words) -----------------------------------
HOOK_OPENERS = [
    "Throw this away.",
    "This costs twelve bucks.",
    "Your expensive gadget is a scam.",
    "Nobody knows about this.",
    "This should be illegal.",
    "Stop overpaying right now.",
    "This fifteen dollar gadget. Wow.",
    "Amazon is hiding this.",
    "I found something insane.",
    "Delete your cart. Buy this instead.",
    "Your wallet will thank me.",
    "This changes everything.",
    "Stop scrolling. Look at this.",
    "Fifty dollars. That's it.",
    "Wait. This actually works?",
    "Don't buy the expensive one.",
    "I tested this for 3 months.",
    "This beat a 500 dollar product.",
    "The cheap version won.",
    "They don't want you finding this.",
]


# ── Main script generation ────────────────────────────────────────────────────
def generate_script(topic: str, attempt: int = 1) -> str | None:
    """Generate a viral 55-65 word script for a 23-26 second video."""
    print(f"🤖 Generating viral script (attempt {attempt}/3)...")

    hook = random.choice(HOOK_OPENERS)
    series = get_series_theme()
    model = _get_model()
    if not model:
        print("❌ No Gemini API keys. Using fallback.")
        return _build_fallback_script(topic)

    examples_text = "\n\n".join(
        f"EXAMPLE:\nTopic: {ex['topic']}\nTitle: {ex['title']}\nScript: {ex['script']}"
        for ex in EXAMPLE_SCRIPTS
    )

    series_note = ""
    if series:
        series_note = f'\nToday\'s series theme: "{series["name"]}" — integrate this angle naturally.\n'

    prompt = f"""You are the scriptwriter for "Tech 8ytees" — a viral Instagram Reels / YouTube Shorts channel.
Niche: {NICHE}
Target audience: {TARGET_AUDIENCE}
Hook formula: {HOOK_FORMULA}

CONTEXT: 80% skip rate. Viewers leave at 2 seconds. Videos must be 23-26 seconds MAX.
{series_note}
STUDY THESE EXAMPLES (notice: short, punchy, 55-65 words):
{examples_text}

=================================================================
TASK: Write a 55-65 word script about: "{topic}"
=================================================================

CRITICAL TIMING: Video MUST be 23-26 seconds. At ~2.5 words/sec → 55 words = 22s, 65 words = 26s.
NEVER exceed 65 words. Count them. If over 65, cut ruthlessly.

EXACT STRUCTURE (every second planned):

Second 0-2: PATTERN INTERRUPT
- Begin with: "{hook}"
- Under 5 words. Shocking. Viewer stops scrolling.

Second 2-5: PROMISE
- Tell them exactly what they'll get. One sentence.
- Example: "This 22 dollar gadget has noise cancelling that beats AirPods."

Second 5-18: PROOF + DELIVERY (2 fast facts)
- IDENTIFY THE PRODUCT: You MUST name the ACTUAL product (brand + model) within the first 10 seconds.
- Example: "They're called the QCY T13, and they're on Amazon."
- Give one specific number (price, review count, battery hours, megapixels).
- Give one comparison to the expensive alternative.
- Short sentences. Fragments OK. "Four K. Waterproof. Twelve dollars."

Second 18-22: LOOP BACK
- Mention the product name AGAIN.
- Echo the hook so the brain wants to rewatch.
- Example: hook was "This costs twelve bucks." → loop: "The T13. Twelve bucks. That's it."

Second 22-26: CTA (use this EXACT text):
"Save this. What should I test next? Comment."

RULES:
- MAX 65 words. This is non-negotiable.
- Contractions: don't, you're, it's, can't
- PRODUCT NAME: You MUST provide a specific, real-world product name (e.g. QCY T13, Anker 521, Baseus 65W, Ugreen Nexode). If the topic is generic, CHOOSE a popular high-rated budget brand and model that fits.
- Include a specific dollar price comparison ($X vs $Y)
- NO filler: never "basically", "actually", "let me tell you"
- NO emojis. NO markdown. PLAIN TEXT only.
- Sound like a friend showing you a deal — not a salesperson.

OUTPUT FORMAT (nothing else):
PRODUCT_NAME: [The specific brand and model name of the $25 gadget, e.g. QCY T13]
TITLE: [max 55 chars, 2 words ALL CAPS]
HOOK_LINE: [first sentence, under 5 words]
SCRIPT: [60-75 words total, starting with hook, ending with CTA. Mention the PRODUCT_NAME at least twice.]
TAGS: [10 comma-separated lowercase tags]
DESCRIPTION: [1 curiosity-gap sentence — must make people tap "more"]
THUMBNAIL_TEXT: [2-3 ALL CAPS words]
CAPTION_HOOK: [1 bold sentence under 80 chars, curiosity gap]
QUESTION: [1 direct question the viewer can answer in one word]
"""

    try:
        response = model.generate_content(prompt)
        script_text = response.text.strip()

        if "SCRIPT:" in script_text:
            body = script_text.split("SCRIPT:")[1].split("TAGS:")[0].strip()
            wc = len(body.split())
            print(f"📝 Script: {wc} words")
            if wc < 45 or wc > 80:
                if attempt < 3:
                    print(f"⚠️  Out of range ({wc}w, need 55-65). Regenerating...")
                    return generate_script(topic, attempt + 1)
                print("⚠️  Accepting despite length — 3 attempts exhausted.")

        return script_text

    except Exception as e:
        err = str(e).lower()
        if ("quota" in err or "resource_exhausted" in err) and attempt <= len(GEMINI_KEYS):
            return generate_script(topic, attempt + 1)
        print(f"❌ Gemini error: {e}")
        return _build_fallback_script(topic)


# ── Dynamic hashtag generation (niche strategy) ──────────────────────────────
def generate_dynamic_hashtags(topic: str) -> str:
    """
    Generate 8 stratified hashtags:
    3 niche (10k-100k posts) + 3 medium (100k-500k) + 2 broad (500k-2M).
    NEVER use hashtags with over 5M posts.
    """
    print("🏷️ Generating niche hashtags...")
    model = _get_model()

    if not model:
        return _fallback_hashtags(topic)

    prompt = f"""Generate exactly 8 Instagram hashtags for a viral tech Reel about: "{topic}"

STRICT RULES:
- 3 NICHE hashtags (10k-100k posts): hyper-specific to the gadget/product
  Examples: #BudgetEarbuds #CheapGadgetFinds #AmazonHiddenGem #AliExpressGadget
- 3 MEDIUM hashtags (100k-500k posts): category-level
  Examples: #BudgetTech #TechDeals #GadgetReview #AffordableTech
- 2 BROAD hashtags (500k-2M posts): reachable broad tags
  Examples: #TechTips #AmazonFinds
- NEVER use tags with 5M+ posts (#Tech, #AI, #Viral, #Reels — these bury your content)
- No spaces inside hashtags. Start each with #.
- Output ONLY the hashtags separated by spaces. No other text.
"""
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
    words = [w.strip(".,!?$") for w in topic.split()[:3] if len(w) > 2]
    niche = " ".join(f"#{w.capitalize()}" for w in words if w)
    return f"{niche} #BudgetGadgets #CheapTechFinds #AmazonHiddenGems #TechDeals #AffordableTech #TechTips #Tech8ytees"


# ── Fallback script ───────────────────────────────────────────────────────────
def _build_fallback_script(topic: str) -> str:
    print("⚠️  Using fallback script (Gemini unavailable).")
    hook = random.choice(HOOK_OPENERS)
    safe = topic[:50]
    return f"""PRODUCT_NAME: Budget Tech Gadget
TITLE: {safe[:45].upper()} — CHEAP
HOOK_LINE: {hook}
SCRIPT: {hook} This gadget costs under 20 dollars and does what the 300 dollar version does. \
I found it on Amazon with 40,000 five star reviews. The build is insane for the price. \
I tested it for two months. It outperformed the expensive one every time. \
Save this. What should I test next? Comment.
TAGS: budget gadgets, cheap tech, amazon finds, hidden gem, tech deals, affordable tech, gadget review, budget tech, tech tips, cheap gadgets
DESCRIPTION: This budget gadget just embarrassed a product that costs 10x more 👀
THUMBNAIL_TEXT: BUDGET BEAST
CAPTION_HOOK: This gadget costs less than lunch but beats $300 products 👀
QUESTION: What overpriced gadget should I expose next?"""


# ── Script parsing ────────────────────────────────────────────────────────────
def parse_script(raw: str) -> dict | None:
    """Parse the Gemini response into a structured dict."""
    if not raw:
        return None

    fields = ["product_name", "title", "hook_line", "script", "tags", "description",
              "thumbnail_text", "caption_hook", "question"]
    data = {f: "" for f in fields}
    current_key = None
    buffer: list[str] = []

    for line in raw.strip().split("\n"):
        matched = False
        for key in fields:
            if line.upper().startswith(key.upper() + ":"):
                if current_key:
                    data[current_key] = " ".join(buffer).strip()
                current_key = key
                buffer = [line.split(":", 1)[-1].strip()]
                matched = True
                break
        if not matched and current_key:
            buffer.append(line.strip())

    if current_key:
        data[current_key] = " ".join(buffer).strip()

    # Fallback for thumbnail_text
    if not data["thumbnail_text"] and data["title"]:
        data["thumbnail_text"] = " ".join(data["title"].split()[:3]).upper()

    # Auto-append CTA if missing
    save_cta = "Save this before you buy your next gadget."
    question_cta = "What gadget should I test next? Comment below."
    if data["script"] and "save this" not in data["script"].lower():
        data["script"] = data["script"].rstrip() + " " + save_cta + " " + question_cta
        print("ℹ️  CTA auto-appended.")

    # Fallback caption hook
    if not data["caption_hook"] and data["title"]:
        data["caption_hook"] = "This budget gadget just embarrassed a product 10x its price 👀"

    # Fallback question
    if not data["question"]:
        data["question"] = "What overpriced gadget should I expose next?"

    wc = len(data["script"].split())
    print(f'✅ Script parsed — "{data["title"]}" ({wc} words)')
    return data
