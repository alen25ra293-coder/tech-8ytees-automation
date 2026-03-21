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
            "Nobody tells you this when you buy AirPods. You're not paying "
            "for better sound. You're paying for the logo. I tested every "
            "cheap earbud out there — the Soundcore Space A40 at sixty bucks "
            "has better bass, longer battery, and noise cancellation that "
            "slaps harder than AirPods. My Apple-obsessed friend tried them "
            "and couldn't go back. The Nothing Ear? Half the price, twice "
            "the personality. And nobody tells you this — until now. "
            "Subscribe, send this to a friend, and follow us on Instagram!"
        ),
    },
    {
        "topic": "AI tools replacing jobs",
        "title": "5 AI Tools QUIETLY Replacing Your Coworkers",
        "hook": "Here's what your boss isn't telling you.",
        "script": (
            "Here's what your boss isn't telling you. Five AI tools are "
            "replacing real people right now. ChatGPT cut junior copywriter "
            "positions by 30 percent. Midjourney killed stock photography "
            "overnight. GitHub Copilot writes 40 percent of new code at "
            "some companies. Perplexity is wrecking SEO blogs. Synthesia "
            "replaced corporate video teams. The winners aren't people who "
            "fight AI — they're the ones using it better than anyone else. "
            "You have about six months. And here's what your boss still "
            "isn't telling you. Subscribe, send this to a friend, "
            "and follow us on Instagram!"
        ),
    },
    {
        "topic": "the $30 gadget that changes your setup",
        "title": "This $30 GADGET Embarrassed My $800 Setup",
        "hook": "Everyone laughed when I plugged this in.",
        "script": (
            "Everyone laughed when I plugged this in. A thirty dollar USB-C "
            "hub that does what my $200 dock couldn't. Dual monitors, SD card "
            "slot, ethernet, and 100 watt passthrough charging. I threw my old "
            "dock in the trash. The build quality? Metal. Not cheap plastic. "
            "It handles 4K at 60Hz without dropping frames. My tech friends asked "
            "where I got it and bought three. The best part? No driver install. "
            "Plug in and forget. Everyone laughed — now they all have one. "
            "Subscribe, send this to a friend, and follow us on Instagram!"
        ),
    },
]

# -- Pattern-interrupt hook openers -------------------------------------------
HOOK_OPENERS = [
    "Nobody talks about this, but",
    "Here's what they don't tell you —",
    "This changed everything for me.",
    "Stop scrolling. This matters.",
    "I almost made a huge mistake.",
    "Wait — before you spend another dollar,",
    "Real talk:",
    "I tested this so you don't have to.",
    "This is going to sound crazy, but",
    "The tech industry is lying to you.",
    "I can't believe nobody talks about this.",
    "You're wasting money every single day.",
    "Okay this blew my mind.",
    "Don't buy anything until you see this.",
    "I switched and I'm never going back.",
    "My friend thought I was crazy — until",
    "Three years ago I made the worst tech mistake of my life.",
    "This $30 gadget embarrassed my $800 setup.",
    "Everyone laughed at me for buying this.",
    "I compared every option. One won by a mile.",
    "Here's the secret pros never share.",
    "I found a cheat code for tech buyers.",
    "Your phone is hiding something from you.",
    "This got my friend to throw out his MacBook.",
    "Here's what million-dollar YouTubers use that you don't.",
    "Delete this app right now.",
    "I was today years old when I learned this.",
    "Your charger is slowly killing your phone.",
    "They removed this feature and nobody noticed.",
    "This free app replaces a $200 subscription.",
]

# -- Fallback topics ----------------------------------------------------------
FALLBACK_TOPICS = [
    # Regret / mistakes
    "The worst tech purchase I ever made",
    "Why I returned my iPhone and switched to Android",
    "Stop buying flagship phones — here's the real reason",
    # Secret / hidden
    "The $30 gadget that pros hide from you",
    "Hidden iPhone features nobody talks about",
    "The smartwatch Apple doesn't want you to own",
    # Money / savings
    "The $50 gadget that beats your laptop",
    "Budget laptop that outperforms expensive ones",
    "Stop buying expensive earbuds — here's why",
    # Change / lifestyle
    "AI tools that will replace your job in 2026",
    "The gadget that made me delete half my apps",
    "This one product made my setup 10x smarter",
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
    """Generate a viral 95-115 word script with hook, loop ending, and CTA."""
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

    prompt = f"""You are the scriptwriter for "Tech 8ytees" — a viral tech YouTube Shorts/Instagram Reels channel.

MISSION: 96% of viewers scroll away in the first 2 seconds. You must BREAK that pattern.

STUDY THESE VIRAL EXAMPLES:
{examples_text}

=================================================================
TASK: Write a viral 95-115 word tech SHORT script about: "{topic}"
=================================================================

TIMING: spoken at ~2.7 words/sec → 100 words ≈ 37 seconds. Max 115 words = 42 seconds.
The final video MUST stay under 45 seconds.

STRUCTURE (follow this exactly):
1. HOOK (first sentence): Begin with "{hook}"
   - MUST be under 8 words and spoken in under 2.5 seconds.
   - Create a "wait, what?" reaction. Use tension, controversy, or a knowledge gap.
2. BODY (2-3 fast punchy points):
   - Real brand names, real dollar/percentage numbers, real specs.
   - Mix sentence lengths: 3-word punches ("Gone. Just like that.") + 12-word details.
   - Each point escalates — the next one is MORE surprising than the last.
3. LOOP ENDING: Echo or callback to the hook (makes rewatching feel natural).
4. CTA (EXACT ending, word-for-word):
   "Subscribe, send this to a friend, and follow us on Instagram!"

ALGORITHM OPTIMISATION (what makes the algorithm push your video):
- Pattern interrupt first 3 words → viewer stops scrolling
- Open loop in hook ("nobody tells you = viewer must stay to find out what)
- Curiosity gap: tease a payoff, deliver mid-video, then twist at end
- Contrast / comparison: cheap vs expensive, old vs new, expected vs reality
- Specific numbers: $47 not "affordable", 40% not "a lot", 3x not "much better"
- Social proof: "my friend tried", "developer at Google said", "1M+ sold"
- Name real products: AirPods, Galaxy, ThinkPad, Anker, Nothing, Pixel, Tesla
- Contractions always: don't, you've, I'm, here's, can't, won't
- NO filler: never use "basically", "actually", "I wanted to", "today we'll"
- NO formal language, NO essay structure, NO passive voice
- NO emojis in script body
- NO markdown: no **bold**, no *italics*, no _underscores_ — PLAIN TEXT ONLY

TITLE RULES:
- Must have 1 number OR 1 question OR 1 emotional trigger word (STOPPED, DESTROYED, KILLED, SECRETLY)
- ALL CAPS on exactly 2-3 key words: "Why I STOPPED Using AirPods", "This $40 Gadget CHANGED Everything"
- Max 65 characters

THUMBNAIL_TEXT RULES:
- Exactly 2-4 ALL CAPS words
- Must create curiosity or shock: "APPLE LIED?!", "RIP AIRPODS", "BYE MACBOOK", "$30 KING"
- No full sentences. No lowercase.

CAPTION_HOOK RULES:
- Single sentence that appears BEFORE the "more" button on Instagram
- Bold claim or cliffhanger, max 100 chars
- Must make someone tap "more": "I threw out my AirPods after finding this 👇"

OUTPUT FORMAT (nothing else, no commentary, no extra text):
TITLE: [max 65 chars, 2-3 words ALL CAPS]
HOOK_LINE: [the first sentence of the script only]
SCRIPT: [95-115 words starting with the hook, ending with the CTA]
TAGS: [10 comma-separated tags]
DESCRIPTION: [2 casual, human sentences — like a comment, not an essay]
THUMBNAIL_TEXT: [2-4 ALL CAPS words]
CAPTION_HOOK: [single punchy sentence, max 100 chars]
"""

    try:
        response = model.generate_content(prompt)
        script_text = response.text.strip()

        if "SCRIPT:" in script_text:
            body = script_text.split("SCRIPT:")[1].split("TAGS:")[0].strip()
            wc = len(body.split())
            print(f"📝 Script: {wc} words")
            if wc < 75 or wc > 145:
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
    return f"""TITLE: {safe[:55].upper()} — The Truth Nobody Tells You
HOOK_LINE: {hook}
SCRIPT: {hook} — {safe} has changed completely in 2026 and most people still don't get it. \
I've been testing this for weeks and honestly, the results surprised even me. \
The budget options right now perform as well as expensive ones did two years ago. \
The gap just doesn't exist anymore. Don't sleep on this category. \
If you haven't revisited this recently, you're leaving real money on the table. \
And just like I said — {hook.lower()} But now you do. \
Subscribe, send this to a friend, and follow us on Instagram!
TAGS: tech, gadgets, review, 2026, shorts, viral, buying guide, budget tech, tech tips, tech news
DESCRIPTION: Can't believe how much {safe} has changed. Drop your questions below — I read every one.
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
