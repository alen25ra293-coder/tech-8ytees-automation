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


# ── Few-shot examples — pattern-interrupt hooks, loop endings ────────────────
EXAMPLE_SCRIPTS = [
    {
        "topic": "best wireless earbuds under $60",
        "title": "I TESTED Every Cheap Earbud So You Don't Have To",
        "hook": "Nobody tells you this when you buy AirPods.",
        "script": (
            "Nobody tells you this when you buy AirPods. You're not paying for better sound. "
            "You're paying for the logo. I've tested every cheap earbud out there and here's the truth — "
            "the Soundcore Space A40 at sixty bucks has better bass, longer battery, and "
            "noise cancellation that slaps harder than AirPods. I gave them to my Apple-obsessed "
            "friend and he couldn't go back. Samsung Galaxy Buds for Android users? No contest. "
            "But the absolute king right now is the Nothing Ear — half the price, "
            "twice the personality. And remember — nobody tells you this, "
            "until now. Smash that subscribe button, send this to a friend who needs to see it, "
            "and follow us on Instagram — links are in the bio!"
        ),
    },
    {
        "topic": "AI tools replacing jobs",
        "title": "5 AI Tools QUIETLY Replacing Your Coworkers",
        "hook": "Here's what your boss isn't telling you.",
        "script": (
            "Here's what your boss isn't telling you. Five AI tools are replacing real people "
            "at real companies right now. ChatGPT already cut junior copywriter positions by "
            "30 percent at dozens of agencies. Midjourney killed stock photography overnight. "
            "GitHub Copilot writes over 40 percent of new code at some companies. Perplexity "
            "is wrecking SEO blogs. Synthesia is replacing corporate video teams. Look — "
            "the winners aren't the people who fight AI. They're the people who use it "
            "better than anyone else. And here's what your boss still isn't telling you: "
            "you have about six months to get ahead of this. "
            "Smash that subscribe button, send this to a friend who needs to see it, "
            "and follow us on Instagram — links are in the bio!"
        ),
    },
]

# -- Pattern-interrupt hook openers -------------------------------------------
HOOK_OPENERS = [
    "Nobody talks about this, but",
    "Here's what they don't tell you --",
    "This changed everything for me.",
    "Stop scrolling. This matters.",
    "I almost made a huge mistake.",
    "Wait -- before you spend another dollar,",
    "Real talk:",
    "I tested this so you don't have to.",
    "This is going to sound crazy, but",
    "The tech industry is lying to you.",
    "I can't believe nobody talks about this.",
    "You're wasting money every single day.",
    "Okay this blew my mind.",
    "Don't buy anything until you see this.",
    "I switched and I'm never going back.",
    "My friend thought I was crazy -- until",
    "Three years ago I made the worst tech mistake of my life.",
    "This $30 gadget embarrassed my $800 setup.",
    "Everyone laughed at me for buying this.",
    "I compared every option. One won by a mile.",
    "Here's the secret pros never share.",
    "I found a cheat code for tech buyers.",
    "Your phone is hiding something from you.",
    "This got my tech-obsessed friend to throw out his MacBook.",
    "Here's what a million-dollar YouTuber uses that you don't.",
]

# -- Fallback topics ----------------------------------------------------------
FALLBACK_TOPICS = [
    # Regret / mistakes
    "The worst tech purchase I ever made",
    "Why I returned my iPhone and switched to Android",
    "Stop buying flagship phones -- here's the real reason",
    # Secret / hidden
    "The $30 gadget that pros hide from you",
    "Hidden iPhone features nobody talks about",
    "The smartwatch Apple doesn't want you to own",
    # Money / savings
    "The $50 gadget that beats your laptop",
    "Budget laptop that outperforms expensive ones",
    "Stop buying expensive earbuds -- here's why",
    # Change / lifestyle
    "AI tools that will replace your job in 2026",
    "The gadget that made me delete half my apps",
    "This one product made my apartment feel 10x smarter",
    # Status
    "The one gadget every programmer secretly uses",
    "The gaming mouse pros use but never talk about",
    "The best headphones for creators that nobody buys",
    # Curiosity
    "What happens if you charge your phone all night",
    "The VR headset that nobody is talking about",
    "The best tech accessories nobody talks about",
    # Comparison / contrast
    "Cheap vs expensive phone: the truth nobody shows you",
    "Wired vs wireless headphones in 2026: you'll be surprised",
    "USB hub vs dock: the $20 difference that changes everything",
]


# ── Main script generation ────────────────────────────────────────────────────
def generate_script(topic: str, attempt: int = 1) -> str | None:
    """Generate a viral 120-145 word script with hook, loop ending, and CTA."""
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

    prompt = f"""You are the scriptwriter for "Tech 8ytees" -- a viral YouTube Shorts/Reels channel.
GOAL: Make viewers STOP scrolling in the first 2 seconds. 96% skip immediately. You must fight that.

STUDY THESE EXAMPLES:
{examples_text}

================================================
TASK: Write a viral 95-115 word script about: "{topic}"
================================================

TARGET: The final video must be 38-45 SECONDS long when spoken.
At natural speech pace (~2.5 words/sec): 100 words = ~40 seconds. DO NOT exceed 115 words.

STRUCTURE (follow exactly):
1. HOOK (first sentence): "{hook}"
   - Must be under 2.5 seconds when spoken. Short, tense, no fluff.
   - Creates instant "wait, what?" in viewer's brain.
2. 2-3 punchy points (real facts, dollar amounts, percentages, brand names)
3. LOOP ENDING (echoes the hook -- makes rewatching feel natural)
4. CTA (EXACT, word-for-word):
   "Smash that subscribe button, send this to a friend who needs to see it, and follow us on Instagram -- links are in the bio!"

RETENTION RULES (what top creators do):
- First 5 words MUST create tension or a knowledge gap
- Use numbers: $47, 40%, 3x better, under 2 weeks
- Name real products and brands with real prices
- Short fragments hit hard: "Gone. Just like that.", "I couldn't go back."
- Contractions always: don't, you've, I'm, here's
- Mix sentence lengths (3-word punches + 15-word sentences)

FORBIDDEN (these kill retention):
- Generic openers: "In today's video", "Let's talk about", "Hey everyone"
- Formal language, passive voice, essay structure
- Long descriptions without drama or tension
- Emojis in the script text
- Filler words: "basically", "actually", "I wanted to", "Today I'll be showing"
- ANY markdown formatting: no **bold**, no *italics*, no _underscores_, no `code` — output PLAIN TEXT ONLY

TITLE RULES:
- Number OR question OR emotional trigger word
- Strong examples: "Why I RETURNED My $1200 Laptop", "5 Gadgets I Use EVERY Day", "This $40 Device Changed Everything"
- ALL CAPS on 2-3 trigger words

OUTPUT FORMAT (nothing else, no extra text):
TITLE: [max 65 chars]
HOOK_LINE: [just the first sentence]
SCRIPT: [95-115 word script starting with the hook]
TAGS: [10 tags, comma-separated]
DESCRIPTION: [2 casual human-sounding sentences]
THUMBNAIL_TEXT: [3-5 ALL CAPS words]
CAPTION_HOOK: [Single punchy Instagram caption opener -- bold claim or curiosity gap, max 120 chars]
"""

    try:
        response = model.generate_content(prompt)
        script_text = response.text.strip()

        if "SCRIPT:" in script_text:
            body = script_text.split("SCRIPT:")[1].split("TAGS:")[0].strip()
            wc = len(body.split())
            print(f"📝 Script: {wc} words")
            if wc < 75 or wc > 140:
                if attempt < 3:
                    print(f"⚠️  Out of range ({wc}w). Regenerating...")
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
    Generate 8 topic-specific hashtags (5 niche + 3 broad).
    Returns a space-separated hashtag string like '#gadgets #tech ...'
    """
    print("🏷️ Generating dynamic hashtags...")
    model = _get_model()

    if not model:
        return _fallback_hashtags(topic)

    prompt = f"""Generate exactly 8 Instagram/YouTube hashtags for a viral tech video about: "{topic}"

Rules:
- 5 NICHE hashtags: directly about the product/topic (e.g. #WirelessEarbuds #AirPodsAlternative)
- 3 BROAD hashtags: wide reach (e.g. #Tech #Gadgets #TechTips)
- No spaces inside hashtags. No '#' prefix for words with spaces.
- Output ONLY the hashtags separated by spaces. Nothing else.
Example output: #WirelessEarbuds #BudgetEarbuds #AirPodsAlternative #SoundcoreReview #NothingEar #Tech #Gadgets #TechReview
"""
    try:
        resp = model.generate_content(prompt)
        tags = resp.text.strip()
        # Validate it looks like hashtags
        if "#" in tags and len(tags) > 10:
            print(f"✅ Hashtags: {tags}")
            return tags
    except Exception:
        pass

    return _fallback_hashtags(topic)


def _fallback_hashtags(topic: str) -> str:
    words = [w.strip(".,!?") for w in topic.split()[:3]]
    niche = " ".join(f"#{w.capitalize()}" for w in words if w)
    broad = "#Tech #Gadgets #TechShorts #Viral #Shorts"
    return f"{niche} {broad} #Tech8ytees #InstagramReels"


# ── Fallback script ───────────────────────────────────────────────────────────
def _build_fallback_script(topic: str) -> str:
    print("⚠️  Using fallback script (Gemini unavailable).")
    hook = random.choice(HOOK_OPENERS)
    safe = topic[:50]
    return f"""TITLE: {safe[:55].upper()} — The Truth Nobody Tells You
HOOK_LINE: {hook}
SCRIPT: {hook} — {safe} has changed completely in 2026 and most people still don't get it. \
I've been testing this for weeks and honestly, the results surprised even me. \
The budget options right now perform as well as expensive ones did two years ago. \
Like the gap just doesn't exist anymore. Don't sleep on this category. \
Look — if you haven't revisited this recently, you're leaving real money on the table. \
And just like I said at the start — {hook.lower()} But now you do. \
Smash that subscribe button, send this to a friend who needs to see it, and follow us on Instagram — links are in the bio!
TAGS: tech, gadgets, review, 2026, shorts, viral, buying guide, recommendations, techy, budget tech
DESCRIPTION: Can't believe how much {safe} has changed. Drop your questions in the comments — I read every single one.
THUMBNAIL_TEXT: {safe[:20].upper()} TRUTH
CAPTION_HOOK: The truth about {safe} that nobody is talking about 👇"""


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
    cta = ("Smash that subscribe button, send this to a friend who needs to see it, "
           "and follow us on Instagram — links are in the bio!")
    if data["script"] and "subscribe button" not in data["script"].lower():
        data["script"] = data["script"].rstrip() + " " + cta
        print("ℹ️  CTA auto-appended (was missing from output).")

    # Fallback caption hook
    if not data["caption_hook"] and data["title"]:
        data["caption_hook"] = f"The truth about this that nobody's talking about 👇"

    wc = len(data["script"].split())
    print(f"✅ Script parsed — \"{data['title']}\" ({wc} words)")
    return data
