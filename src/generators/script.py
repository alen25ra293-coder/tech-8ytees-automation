"""
Script Generator — viral YouTube Shorts / Instagram Reels scripts.
Enforces human-sounding language, pattern-interrupt hooks, loop endings,
dynamic hashtags, and strong title optimization.
"""
import os
import random
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


# ── Few-shot examples — SHORT, punchy, 80-95 words ──────────────────────────
EXAMPLE_SCRIPTS = [
    {
        "topic": "best wireless earbuds under $60",
        "title": "I TESTED Every Cheap Earbud So You Don't Have To",
        "hook": "Stop buying AirPods.",
        "script": (
            "Stop buying AirPods. You're paying for a logo. Not sound. "
            "I tested 30 earbuds this year — the Soundcore Space A40 at "
            "sixty bucks has punchier bass, better noise cancellation, "
            "and ten hours of battery. My Apple-obsessed friend tried them. "
            "Hasn't touched his AirPods since. The Nothing Ear? Half the "
            "price. Twice the personality. Transparent design that looks "
            "insane. You've been overpaying for years and nobody told you. "
            "Until now. Subscribe, send this to a friend, and follow us "
            "on Instagram!"
        ),
    },
    {
        "topic": "the $30 gadget that changes your setup",
        "title": "This $30 GADGET Embarrassed My $800 Setup",
        "hook": "Everyone laughed when I plugged this in.",
        "script": (
            "Everyone laughed when I plugged this in. A thirty dollar USB-C "
            "hub. Dual monitors. SD card. Ethernet. 100 watt passthrough. "
            "My 200 dollar dock couldn't do half of that. Build quality? "
            "Full metal. Not cheap plastic. 4K at 60 hertz. Zero frame "
            "drops. Three of my friends bought one the same day. No drivers. "
            "Plug in and forget. Everyone laughed — now they all have one. "
            "Subscribe, send this to a friend, and follow us on Instagram!"
        ),
    },
]

# -- Pattern-interrupt hook openers (SHORT — under 6 words) --------------------
HOOK_OPENERS = [
    "Stop buying this.",
    "They lied to you.",
    "Delete this app now.",
    "Nobody will tell you this.",
    "This should be illegal.",
    "You're wasting your money.",
    "I was wrong about everything.",
    "This changes everything.",
    "Your phone is lying to you.",
    "Throw this away immediately.",
    "Don't buy this. Seriously.",
    "I almost got scammed.",
    "This killed my old setup.",
    "Everyone's sleeping on this.",
    "Wait. Don't scroll.",
    "Your charger is destroying your phone.",
    "I returned my MacBook for this.",
    "This costs thirty bucks.",
    "Apple doesn't want you seeing this.",
    "I can't unsee this.",
]

# -- Fallback topics ----------------------------------------------------------
FALLBACK_TOPICS = [
    "The worst tech purchase I ever made",
    "Why I returned my iPhone and switched to Android",
    "Stop buying flagship phones — here's the real reason",
    "The $30 gadget that pros hide from you",
    "Hidden iPhone features nobody talks about",
    "The $50 gadget that beats your laptop",
    "Budget laptop that outperforms expensive ones",
    "Stop buying expensive earbuds — here's why",
    "AI tools that will replace your job in 2026",
    "Cheap vs expensive phone: the truth nobody shows you",
]


# ── Main script generation ────────────────────────────────────────────────────
def generate_script(topic: str, attempt: int = 1) -> str | None:
    """Generate a viral 80-95 word script for a 35-40 second video."""
    print(f"🤖 Generating viral script (attempt {attempt}/3)...")

    hook = random.choice(HOOK_OPENERS)
    model = _get_model()
    if not model:
        print("❌ No Gemini API keys. Using fallback.")
        return _build_fallback_script(topic)

    examples_text = "\n\n".join(
        f"EXAMPLE:\nTopic: {ex['topic']}\nTitle: {ex['title']}\nHook: {ex['hook']}\nScript: {ex['script']}"
        for ex in EXAMPLE_SCRIPTS
    )

    prompt = f"""You are the scriptwriter for "Tech 8ytees" — a viral tech YouTube Shorts channel.

CONTEXT: Our videos have an 80% skip rate. Viewers leave at the 2-second mark. You MUST fix this.

STUDY THESE VIRAL EXAMPLES (notice the short, punchy hooks):
{examples_text}

=================================================================
TASK: Write a SHORT, PUNCHY, 80-95 word script about: "{topic}"
=================================================================

CRITICAL TIMING: The final video MUST be 35-40 seconds. NOT longer.
At ~2.5 words/sec → 80 words = 32s, 95 words = 38s. Stay in this range.

STRUCTURE (follow EXACTLY):

1. HOOK (first 2 seconds — this is LIFE OR DEATH):
   - Begin with: "{hook}"
   - MUST be under 6 words. Spoken in under 2 seconds.
   - The viewer decides to stay or leave in this moment. Make it visceral.
   - Pattern interrupts that work: bold claims, controversy, direct commands, shocking statements.
   - BAD hooks: "Hey guys today we're looking at..." / "So I found this cool thing..."
   - GOOD hooks: "Stop buying AirPods." / "They lied to you." / "Delete this app now."

2. BODY (2 fast points ONLY — no more):
   - Real brand names. Real dollar amounts. Real specs.
   - Short sentences. Fragments are good. "Gone. Just like that."
   - Point 2 must be MORE surprising than point 1 (escalation).
   - DO NOT ramble. Every single word must earn its place.

3. LOOP ENDING (1 sentence):
   - Echo the hook so the viewer feels pulled to rewatch.

4. CTA (EXACT words, do not change):
   "Subscribe, send this to a friend, and follow us on Instagram!"

WRITING RULES:
- Contractions always: don't, you've, I'm, here's, can't
- Specific numbers: $47 not "affordable", 40% not "a lot"
- Name real products: AirPods, Galaxy, Anker, Nothing, Pixel
- NO filler words: never "basically", "actually", "I wanted to", "today we'll", "let me tell you"
- NO formal language. NO passive voice. NO emojis. NO markdown.
- Sound like a friend ranting, not a presenter reading a script.

OUTPUT FORMAT (nothing else):
TITLE: [max 60 chars, 2-3 words ALL CAPS]
HOOK_LINE: [first sentence only, under 6 words]
SCRIPT: [80-95 words, starting with hook, ending with CTA]
TAGS: [10 comma-separated tags]
DESCRIPTION: [2 casual sentences]
THUMBNAIL_TEXT: [2-3 ALL CAPS words]
CAPTION_HOOK: [punchy sentence, max 80 chars]
"""

    try:
        response = model.generate_content(prompt)
        script_text = response.text.strip()

        if "SCRIPT:" in script_text:
            body = script_text.split("SCRIPT:")[1].split("TAGS:")[0].strip()
            wc = len(body.split())
            print(f"📝 Script: {wc} words")
            if wc < 60 or wc > 120:
                if attempt < 3:
                    print(f"⚠️  Out of range ({wc}w, need 80-95). Regenerating...")
                    return generate_script(topic, attempt + 1)
                print("⚠️  Accepting despite length — 3 attempts exhausted.")

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
    Generate 12 topic-specific hashtags (5 niche + 4 medium + 3 broad).
    Returns a space-separated hashtag string like '#gadgets #tech ...'
    """
    print("🏷️ Generating dynamic hashtags...")
    model = _get_model()

    if not model:
        return _fallback_hashtags(topic)

    prompt = f"""Generate exactly 12 Instagram/YouTube hashtags for a viral tech video about: "{topic}"

Rules:
- 5 NICHE hashtags: directly about the specific product/topic (e.g. #SoundcoreA40 #AirPodsAlternative #BudgetEarbuds2026)
- 4 MEDIUM hashtags: category-level reach (e.g. #WirelessEarbuds #TechReview #GadgetReview #BestEarbuds)
- 3 BROAD hashtags: maximum reach (e.g. #Tech #Shorts #Viral)
- No spaces inside hashtags. Start each with #.
- Mix trending and evergreen hashtags.
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
    words = [w.strip(".,!?") for w in topic.split()[:3]]
    niche = " ".join(f"#{w.capitalize()}" for w in words if w)
    broad = "#Tech #Gadgets #TechShorts #Viral #Shorts #TechTok #TechReview"
    return f"{niche} {broad} #Tech8ytees #Reels"


# ── Fallback script ───────────────────────────────────────────────────────────
def _build_fallback_script(topic: str) -> str:
    print("⚠️  Using fallback script (Gemini unavailable).")
    hook = random.choice(HOOK_OPENERS)
    safe = topic[:50]
    return f"""TITLE: {safe[:55].upper()} — The TRUTH
HOOK_LINE: {hook}
SCRIPT: {hook} {safe} has changed completely in 2026. Most people still don't get it. \
I've been testing this for weeks. The results surprised even me. \
Budget options now perform as well as expensive ones did two years ago. The gap? Gone. \
If you haven't revisited this recently, you're leaving money on the table. \
And just like I said — {hook.lower()} But now you do. \
Subscribe, send this to a friend, and follow us on Instagram!
TAGS: tech, gadgets, review, 2026, shorts, viral, budget tech, tech tips, tech news, comparison
DESCRIPTION: Can't believe how much {safe} has changed. Drop your questions below.
THUMBNAIL_TEXT: {safe[:15].upper()} TRUTH
CAPTION_HOOK: The truth about {safe} that nobody's talking about 👇"""


# ── Script parsing ────────────────────────────────────────────────────────────
def parse_script(raw: str) -> dict | None:
    """Parse the Gemini response into a structured dict."""
    if not raw:
        return None

    fields = ["title", "hook_line", "script", "tags", "description",
              "thumbnail_text", "caption_hook"]
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
        data["thumbnail_text"] = " ".join(data["title"].split()[:4]).upper()

    # Auto-append CTA if Gemini forgot it
    cta = "Subscribe, send this to a friend, and follow us on Instagram!"
    if data["script"] and "subscribe" not in data["script"].lower():
        data["script"] = data["script"].rstrip() + " " + cta
        print("ℹ️  CTA auto-appended (was missing from output).")

    # Fallback caption hook
    if not data["caption_hook"] and data["title"]:
        data["caption_hook"] = f"The truth about this that nobody's talking about 👇"

    wc = len(data["script"].split())
    print(f"✅ Script parsed — \"{data['title']}\" ({wc} words)")
    return data
