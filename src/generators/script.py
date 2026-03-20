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

# ── Pattern-interrupt hook openers ───────────────────────────────────────────
HOOK_OPENERS = [
    "Nobody talks about this, but",
    "Here's what they don't tell you —",
    "This changed everything for me.",
    "Stop what you're doing and listen.",
    "I almost made a huge mistake.",
    "Here's the thing nobody tells you —",
    "Wait — before you buy anything,",
    "Real talk:",
    "I tested this so you don't have to.",
    "This is going to sound crazy, but",
]

# ── Fallback topics ───────────────────────────────────────────────────────────
FALLBACK_TOPICS = [
    "The $50 gadget that beats your laptop",
    "Hidden iPhone features nobody talks about",
    "Stop buying expensive earbuds — here's why",
    "The smartwatch Apple doesn't want you to own",
    "AI tools that will replace your job in 2026",
    "The gaming mouse pros secretly use",
    "Mechanical keyboards are a luxury scam",
    "Budget laptop that outperforms expensive ones",
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

    prompt = f"""You are the scriptwriter for viral YouTube Shorts channel "Tech 8ytees".
Your scripts sound like a smart friend talking to you — NEVER like an article, review, or AI.

STUDY THESE EXAMPLES:
{examples_text}

══════════════════════════════════════════════
TASK: Write a viral 125-145 word script about: "{topic}"
══════════════════════════════════════════════

STRUCTURE (follow exactly):
1. 🎣 HOOK (first sentence — use this exact opener): "{hook}"
2. 📌 2-3 punchy points (conversational, short, real)
3. 🔁 LOOP ENDING (second-to-last sentence must echo the hook so rewatching feels natural)
4. 📣 CTA (EXACT last sentence, word-for-word, no changes):
   "Smash that subscribe button, send this to a friend who needs to see it, and follow us on Instagram — links are in the bio!"

LANGUAGE RULES:
✅ Contractions always: don't, you've, I'm, here's, that's, we're
✅ Casual bridges: "Look,", "Honestly,", "Real talk:", "Here's the thing —"
✅ Short fragments. Personal pronouns. Slang is fine.
✅ Vary sentence length (mix 3-word punches with 15-word sentences)

FORBIDDEN (never ever use):
❌ "In conclusion", "Furthermore", "It's worth noting", "This device provides"
❌ Passive voice. Formal language. Essay structure.
❌ Emojis in the script text.

TITLE RULES (write the most clickable title possible):
- Include a number OR a question OR an emotional trigger word
- Examples of strong title types: "I Tested 7 Earbuds — Here's the Truth", "Why I REGRET Buying This", "The Gadget Nobody Warned Me About"
- ALL CAPS on 2-3 key trigger words

OUTPUT FORMAT (nothing else, no extra text):
TITLE: [max 65 chars — number/question/emotional trigger, ALL CAPS key words]
HOOK_LINE: [just the first sentence — the exact hook used]
SCRIPT: [125-145 word full script starting with the hook]
TAGS: [10 tags — mix of 5 niche + 5 broad, comma-separated]
DESCRIPTION: [2 casual human-sounding sentences]
THUMBNAIL_TEXT: [3-5 ALL CAPS words that would look great on a thumbnail]
CAPTION_HOOK: [Single punchy first line for Instagram caption — curiosity gap or bold claim, max 120 chars]
"""

    try:
        response = model.generate_content(prompt)
        script_text = response.text.strip()

        if "SCRIPT:" in script_text:
            body = script_text.split("SCRIPT:")[1].split("TAGS:")[0].strip()
            wc = len(body.split())
            print(f"📝 Script: {wc} words")
            if wc < 90 or wc > 210:
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
