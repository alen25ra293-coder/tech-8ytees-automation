"""
Script Generator — Tech 8ytees
Viral 23-26 second scripts optimized for <20% skip rate.
Niche: Budget gadgets and hidden tech gems under ₹2000 / $25 that replace expensive products.

RULES ENFORCED:
- NO banned words: destroys, shames, embarrasses, you won't believe
- 5-section structure: HOOK → PROBLEM → SOLUTION → DEMO → PAYOFF
- Visual instructions per line
- 50–70 word script
- Indian ₹ and USD $ pricing
"""
import os
import random
from datetime import date

# ── API key rotation ─────────────────────────────────────────────────────────
_gemini_keys_raw = (
    os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
)
GEMINI_KEYS = [k.strip() for k in _gemini_keys_raw.split(",") if k.strip()]
_key_index = 0

# ── Banned words — must NEVER appear in output ────────────────────────────────
BANNED_WORDS = ["destroys", "shames", "embarrasses", "won't believe", "will blow your mind"]


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
        print("⚠️  google-generativeai not installed. Using fallback.")
        return None
    key = _next_key()
    if not key:
        return None
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-2.5-flash")


# ── Niche constants ──────────────────────────────────────────────────────────
NICHE = "budget gadgets and hidden tech gems under ₹2000 / $25 that most people don't know about"
TARGET_AUDIENCE = "16-35 year old Indian viewers who want the best tech without spending a lot"

# ── Niche-specific topics ────────────────────────────────────────────────────
NICHE_TOPICS = [
    # Audio
    "₹1799 earbuds with noise cancelling that rivals ₹20,000 AirPods Pro",
    "₹999 Bluetooth speaker that sounds like a ₹8,000 JBL Charge",
    "₹1,499 gaming headset that beats ₹5,000 HyperX Cloud",
    "₹800 wireless earbuds with 40hr battery nobody talks about",
    # Phone accessories
    "₹499 wireless charger faster than ₹3,500 Apple MagSafe",
    "₹699 magnetic phone mount that beats every car mount",
    "₹999 phone camera lens kit that replaces a ₹50,000 DSLR",
    "₹399 screen protector that's better than ₹1,200 branded ones",
    # Desktop / Productivity
    "₹999 USB-C hub that does what a ₹6,000 docking station does",
    "₹1,799 keyboard that types better than ₹12,000 mechanicals",
    "₹1,299 webcam that beats ₹7,000 Logitech C920",
    "₹899 desk lamp with wireless charging nobody knows about",
    "₹299 cable organizer that fixes your messy desk forever",
    # Video / Cameras
    "₹1,499 action camera that shoots 4K like a ₹30,000 GoPro",
    "₹1,999 ring light that makes you look like a studio setup",
    "₹2,499 mini projector that replaces your bedroom TV",
    # Smart Home
    "₹699 smart plug that cuts your electricity bill in half",
    "₹499 LED strip lights that transform any room instantly",
    "₹799 smart bulb cheaper and better than Philips Hue",
    # Portable
    "₹1,299 power bank that charges 3 devices at once",
    "₹999 handheld fan that's basically portable AC",
    "₹1,999 portable SSD faster than most laptop internal drives",
    "₹599 Bluetooth tracker that beats ₹3,500 AirTag",
    # Random hidden gems
    "₹499 phone cooling fan for gaming that actually works",
    "₹299 mini vacuum cleaner for keyboard and desk",
    "₹799 smart water bottle with hydration reminders",
    "₹1,499 instant-print Polaroid camera alternative",
    "₹599 foldable phone stand that beats ₹2,000 premium stands",
]

# ── Series content rotation ──────────────────────────────────────────────────
SERIES_THEMES = {
    5: {"name": "Hidden Gem Saturday",       "hashtag": "#HiddenGem"},
    6: {"name": "Hidden Gem Sunday",          "hashtag": "#HiddenGem"},
    0: {"name": "Budget Find Monday",         "hashtag": "#BudgetFind"},
    1: {"name": "Cheap vs Expensive Tuesday", "hashtag": "#CheapVsExpensive"},
    2: {"name": "Cheap vs Expensive Wednesday","hashtag": "#CheapVsExpensive"},
    3: {"name": "Gadget Swap Thursday",       "hashtag": "#GadgetSwap"},
    4: {"name": "Deal Friday",                "hashtag": "#TechDealFriday"},
}

# ── 5-style hook rotation (never repeat same style twice in a row) ────────────
HOOK_STYLES = {
    "Warning":    [
        "Don't buy a ₹{high_price} {product} yet…",
        "Stop. Don't touch that {product}.",
        "Before you order that — watch this.",
    ],
    "Curiosity":  [
        "I found a cheaper way to {task}…",
        "Nobody told me this existed.",
        "This changed how I use my phone.",
    ],
    "Comparison": [
        "₹{low_price} vs ₹{high_price}. Same result.",
        "This costs ₹{low_price}. That costs ₹{high_price}.",
        "Cheap version vs expensive version — let's go.",
    ],
    "Discovery":  [
        "Nobody is talking about this gadget.",
        "I found this buried on Amazon.",
        "This product has zero hype. It should.",
    ],
    "Challenge":  [
        "Can this ₹{low_price} gadget replace {expensive_product}?",
        "I challenged a ₹{low_price} gadget to beat ₹{high_price}.",
        "Can the cheapest version actually win?",
    ],
}

_LAST_HOOK_STYLE = None


def _pick_hook_opener() -> tuple[str, str]:
    """Return (hook_line, hook_style) — avoids repeating the same style twice."""
    global _LAST_HOOK_STYLE
    styles = list(HOOK_STYLES.keys())
    if _LAST_HOOK_STYLE:
        styles = [s for s in styles if s != _LAST_HOOK_STYLE] or styles
    style = random.choice(styles)
    _LAST_HOOK_STYLE = style
    hook_line = random.choice(HOOK_STYLES[style])
    return hook_line, style


def get_series_theme():
    """Get today's series theme based on day of week."""
    weekday = date.today().weekday()
    theme = SERIES_THEMES.get(weekday)
    if theme:
        print(f"📅 Series: {theme['name']} ({theme['hashtag']})")
    return theme


# ── Few-shot examples — 5-section structure, no banned words ──────────────────
EXAMPLE_SCRIPTS = [
    {
        "topic": "₹1,799 earbuds that rival ₹20,000 AirPods Pro",
        "title": "₹1,799 Earbuds Beat AirPods Pro",
        "script": (
            "Don't buy AirPods yet. "  # HOOK
            "Most people spend ₹20,000 on earbuds just for the logo. "  # PROBLEM
            "These QCY T13s cost ₹1,799 and have noise cancelling, 30-hour battery, "
            "and sound that's genuinely hard to tell apart from AirPods Pro. "  # SOLUTION + DEMO
            "Six million sold. I've used them for 3 months. Never touched my AirPods since. "  # PAYOFF
            "Save this. What should I test next? Comment."  # CTA
        ),
    },
    {
        "topic": "₹1,499 action camera that shoots 4K like a ₹30,000 GoPro",
        "title": "₹1,499 Camera vs ₹30,000 GoPro",
        "script": (
            "Before you buy a GoPro — stop. "  # HOOK
            "₹30,000 for a camera most people use once is a bad deal. "  # PROBLEM
            "This ₹1,499 SJCAM C300 shoots 4K, is waterproof, and fits in your pocket. "  # SOLUTION
            "I took it to Goa. People thought the footage was from a Hero 12. It wasn't. "  # DEMO
            "Same shots. One-twentieth of the price. "  # PAYOFF
            "Save this. What should I test next? Comment."  # CTA
        ),
    },
]

# ── 5 video ideas output format ────────────────────────────────────────────────
FIVE_VIDEO_IDEAS = """
Video 1 — Hook Style: WARNING
Topic: Don't buy a ₹50,000 camera yet — this ₹1,499 gadget shoots the same 4K.
Titles:
  1. This ₹1,499 Camera Replaced My ₹50,000 Setup
  2. Stop Buying Expensive Cameras — Use This Instead
  3. I Tested the Cheapest Alternative to GoPro
Hook Line: Don't buy a GoPro yet.
Script:
  HOOK: Don't buy a GoPro yet.
  PROBLEM: Most travel creators spend ₹30,000 on a camera they use 3 times.
  SOLUTION: This SJCAM C300 costs ₹1,499, shoots 4K, and fits in your shirt pocket.
  DEMO: I took it to Leh and Goa. The footage? People thought it was a GoPro Hero 12.
  PAYOFF: One-twentieth of the price. Zero compromise. Save this before your next trip.
Hashtags: #BudgetCamera #CheapGadgets #TechFinds #GadgetReview #AffordableTech

Video 2 — Hook Style: CURIOSITY
Topic: I found a cheaper way to get studio-quality sound at home.
Titles:
  1. This ₹999 Mic Replaced My ₹8,000 Studio Setup
  2. Stop Overspending on Audio — Use This Instead
  3. I Tested the Cheapest Microphone That Actually Works
Hook Line: Nobody told me this mic existed.
Script:
  HOOK: Nobody told me this mic existed.
  PROBLEM: Most people spend ₹5,000–₹8,000 for a decent mic.
  SOLUTION: The MAONO AU-A04 costs ₹999 and sounds like a ₹6,000 Blue Yeti.
  DEMO: I recorded a voiceover. My editor couldn't tell the difference. 47,000 reviews. Rated 4.5 stars.
  PAYOFF: ₹999 for studio sound. Save this. What should I test next? Comment.
Hashtags: #BudgetMic #CheapTech #HomeStudio #AmazonFind #AffordableTech

Video 3 — Hook Style: COMPARISON
Topic: ₹499 vs ₹3,500 — both charge your phone. One wins by a lot.
Titles:
  1. This ₹499 Charger Is Faster Than Apple MagSafe
  2. Stop Buying Expensive Chargers — Use This Instead
  3. I Tested the Cheapest Wireless Charger vs MagSafe
Hook Line: ₹499 vs ₹3,500. Same speed.
Script:
  HOOK: ₹499 versus ₹3,500. Same result.
  PROBLEM: Apple charges you ₹3,500 for a charging pad. That's just wrong.
  SOLUTION: This Portronics wireless charger costs ₹499 and charges at 15W — same as MagSafe.
  DEMO: I timed both charging an iPhone 13. 2 minutes faster on the ₹499 charger. Not kidding.
  PAYOFF: Save ₹3,000. Use this instead. What overpriced accessory should I test next?
Hashtags: #CheapVsExpensive #WirelessCharger #BudgetTech #TechDeals #AmazonIndia

Video 4 — Hook Style: DISCOVERY
Topic: Nobody is talking about this ₹799 smart plug that cut my electricity bill.
Titles:
  1. This ₹799 Smart Plug Cut My Bill By 30%
  2. The Gadget That Pays for Itself in One Month
  3. Hidden Smart Home Gem Nobody Knows About
Hook Line: Nobody is talking about this gadget.
Script:
  HOOK: Nobody is talking about this gadget. But they should be.
  PROBLEM: Most people don't realize which appliances are draining power 24/7.
  SOLUTION: This Tapo P115 smart plug costs ₹799 and tracks real-time power usage.
  DEMO: I plugged in my AC and TV. Found I was wasting ₹300/month on standby power. Fixed it instantly.
  PAYOFF: One ₹799 plug saved ₹300 a month. Pays for itself in 3 weeks. Save this.
Hashtags: #SmartHome #TechFinds #SaveMoney #BudgetGadgets #HiddenGem

Video 5 — Hook Style: CHALLENGE
Topic: Can this ₹1,799 keyboard replace a ₹15,000 mechanical?
Titles:
  1. ₹1,799 Keyboard vs ₹15,000 Mechanical — Who Wins?
  2. I Challenged a Cheap Keyboard to Beat an Expensive One
  3. Is This the Best Budget Keyboard Under ₹2,000?
Hook Line: Can the cheapest keyboard actually win?
Script:
  HOOK: Can a ₹1,799 keyboard beat a ₹15,000 one? I tested it.
  PROBLEM: Most people think you need to spend big to get a real mechanical keyboard.
  SOLUTION: The Zebronics ZEB-MAX PRO costs ₹1,799 and has clicky switches, RGB, and a metal body.
  DEMO: I typed on it for 2 weeks straight. Zero complaints. My ₹15,000 Keychron stayed in the bag.
  PAYOFF: ₹1,799. Metal build. Clicky switches. You don't need to spend more. Save this.
Hashtags: #BudgetKeyboard #MechanicalKeyboard #TechDeals #GadgetReview #AffordableTech
"""


# ── Main script generation ────────────────────────────────────────────────────
def generate_script(topic: str, attempt: int = 1) -> str | None:
    """Generate a viral 50-70 word script for a 23-26 second video."""
    print(f"🤖 Generating viral script (attempt {attempt}/3)...")

    hook_opener, hook_style = _pick_hook_opener()
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

    prompt = f"""You are the scriptwriter for "Tech 8ytees" — a viral YouTube Shorts channel.
Niche: {NICHE}
Target audience: {TARGET_AUDIENCE}
Today's hook style: {hook_style}

CONTEXT: 80% skip rate. Viewers decide in 2 seconds. Videos must be 23-26 seconds MAX.
{series_note}
⚠️ ABSOLUTE RULES — VIOLATING ANY OF THESE IS UNACCEPTABLE:
1. BANNED WORDS — NEVER USE: "destroys", "shames", "embarrasses", "you won't believe", "will blow your mind"
2. MAX 70 WORDS. Count them. Cut ruthlessly if over.
3. Product name MUST appear within first 10 seconds of script.
4. Prices MUST be in ₹ (Indian Rupees). Example: "₹1,499" or "₹30,000".
5. NO filler: never "basically", "actually", "let me tell you", "so guys"
6. NO emojis. NO markdown. PLAIN TEXT only.
7. Sound like a friend showing a deal — not a salesperson or influencer.

STUDY THESE EXAMPLES (5-section structure, punchy, 55-65 words):
{examples_text}

=================================================================
TASK: Write a 50-70 word script about: "{topic}"
Hook style this video: {hook_style} → start with something like: "{hook_opener}"
=================================================================

MANDATORY 5-SECTION STRUCTURE (every section needed):

SECTION 1 — HOOK (0-2 sec, max 5 words):
Pattern interrupt. Viewer STOPS scrolling. Use the {hook_style} hook style.

SECTION 2 — PROBLEM (2-5 sec):
Call out the specific pain point. Why do people overpay for this?

SECTION 3 — SOLUTION (5-12 sec):
Name the ACTUAL product (brand + model). State the price. One specific spec.

SECTION 4 — DEMO/RESULT (12-20 sec):
One specific test or result. A number, a comparison, a moment. Benefit > feature.

SECTION 5 — PAYOFF + CTA (20-26 sec):
Strong close. Echo the hook. End with: "Save this. What should I test next? Comment."

OUTPUT FORMAT (nothing else, exactly these fields):
PRODUCT_NAME: [specific brand and model, e.g. QCY T13]
TITLE: [max 55 chars, punchy, no banned words]
HOOK_LINE: [first sentence only, under 5 words]
HOOK_STYLE: [{hook_style}]
SCRIPT: [50-70 words, 5-section structure, plain text]
VISUAL_INSTRUCTIONS: [5 lines, one per section: e.g. "HOOK: Zoom in fast on product box | PROBLEM: Cut to confused face | SOLUTION: Show product close-up | DEMO: Side-by-side comparison | PAYOFF: Slow zoom out, text overlay"]
TAGS: [exactly 6 comma-separated lowercase hashtags — 2 niche, 2 mid, 2 broad]
DESCRIPTION: [1 curiosity-gap sentence under 100 chars — makes people tap "more"]
THUMBNAIL_TEXT: [2-3 ALL CAPS words]
CAPTION_HOOK: [1 bold sentence under 80 chars, curiosity gap, no banned words]
QUESTION: [1 direct question viewer can answer in 1-2 words]
"""

    try:
        response = model.generate_content(prompt)
        script_text = response.text.strip()

        # ── Check word count ──────────────────────────────────────────────
        if "SCRIPT:" in script_text:
            body = script_text.split("SCRIPT:")[1].split("VISUAL_INSTRUCTIONS:")[0].strip()
            # Also handle if TAGS comes directly after SCRIPT
            if "TAGS:" in body:
                body = body.split("TAGS:")[0].strip()
            wc = len(body.split())
            print(f"📝 Script: {wc} words")
            if wc < 45 or wc > 80:
                if attempt < 3:
                    print(f"⚠️  Out of range ({wc}w, need 50-70). Regenerating...")
                    return generate_script(topic, attempt + 1)
                print("⚠️  Accepting despite length — 3 attempts exhausted.")

        # ── Check for banned words ────────────────────────────────────────
        raw_lower = script_text.lower()
        found_banned = [bw for bw in BANNED_WORDS if bw in raw_lower]
        if found_banned:
            if attempt < 3:
                print(f"⚠️  Banned words found: {found_banned}. Regenerating...")
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
    """
    Generate 6 stratified hashtags:
    2 niche (10k–100k posts) + 2 medium (100k–500k) + 2 broad (500k–2M).
    NEVER use hashtags with over 5M posts.
    """
    print("🏷️ Generating niche hashtags...")
    model = _get_model()

    if not model:
        return _fallback_hashtags(topic)

    prompt = f"""Generate exactly 6 Instagram/YouTube hashtags for a viral tech Short about: "{topic}"

STRICT RULES:
- 2 NICHE hashtags (10k-100k posts): hyper-specific to the gadget/product
  Examples: #BudgetEarbuds #CheapGadgetFinds #AmazonIndiaTech #HiddenTechGem
- 2 MEDIUM hashtags (100k-500k posts): category-level
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
    words = [w.strip(".,!?$₹") for w in topic.split()[:3] if len(w) > 2]
    niche = " ".join(f"#{w.capitalize()}" for w in words if w)
    return f"{niche} #BudgetGadgets #CheapTechFinds #AmazonIndia #TechDeals #AffordableTech #Tech8ytees"


# ── Fallback script ───────────────────────────────────────────────────────────
def _build_fallback_script(topic: str) -> str:
    print("⚠️  Using fallback script (Gemini unavailable).")
    hook_opener, hook_style = _pick_hook_opener()
    safe = topic[:50]
    return f"""PRODUCT_NAME: Budget Tech Gadget
TITLE: {safe[:45]} — Under ₹2000
HOOK_LINE: Stop. Look at this.
HOOK_STYLE: {hook_style}
SCRIPT: Stop. Look at this. This gadget costs under ₹1,500 and does what the ₹15,000 version does. Found it on Amazon with 40,000 five-star reviews. The build quality is insane for the price. I tested it for two months — it outperformed the expensive one every single time. Save this. What should I test next? Comment.
VISUAL_INSTRUCTIONS: HOOK: Fast zoom in on product | PROBLEM: Cut to shocked face | SOLUTION: Show product box close-up | DEMO: Side-by-side with expensive product | PAYOFF: Text overlay with both prices
TAGS: budgetgadgets, cheaptech, amazonindia, hiddengem, techdeals, affordabletech
DESCRIPTION: This gadget costs 10x less and somehow does the job better 👀
THUMBNAIL_TEXT: BUDGET BEAST
CAPTION_HOOK: This gadget costs less than lunch but beats ₹15,000 products 👀
QUESTION: What overpriced gadget should I expose next?"""


# ── Script parsing ────────────────────────────────────────────────────────────
def parse_script(raw: str) -> dict | None:
    """Parse the Gemini response into a structured dict."""
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
                    data[current_key] = " ".join(buffer).strip()
                current_key = key
                buffer = [line.split(":", 1)[-1].strip()]
                matched = True
                break
        if not matched and current_key:
            buffer.append(line.strip())

    if current_key:
        data[current_key] = " ".join(buffer).strip()

    # ── Fallbacks ─────────────────────────────────────────────────────────────
    if not data["thumbnail_text"] and data["title"]:
        data["thumbnail_text"] = " ".join(data["title"].split()[:3]).upper()

    if not data["caption_hook"] and data["title"]:
        data["caption_hook"] = "This budget gadget just did something a product 10x its price couldn't 👀"

    if not data["question"]:
        data["question"] = "What overpriced gadget should I test next?"

    if not data["visual_instructions"]:
        data["visual_instructions"] = (
            "HOOK: Fast zoom in on product | PROBLEM: Cut to person looking frustrated | "
            "SOLUTION: Show product box and specs | DEMO: Side-by-side comparison clip | "
            "PAYOFF: Text overlay with price difference"
        )

    # ── Auto-append CTA if missing ────────────────────────────────────────────
    save_cta = "Save this. What should I test next? Comment."
    if data["script"] and "save this" not in data["script"].lower():
        data["script"] = data["script"].rstrip() + " " + save_cta
        print("ℹ️  CTA auto-appended.")

    # ── Banned word check on final output ─────────────────────────────────────
    script_lower = data["script"].lower()
    found_banned = [bw for bw in BANNED_WORDS if bw in script_lower]
    if found_banned:
        print(f"⚠️  WARNING: Banned words still in parsed script: {found_banned}")

    wc = len(data["script"].split())
    print(f'✅ Script parsed — "{data["title"]}" ({wc} words) | Hook: {data.get("hook_style","?")}')
    return data
