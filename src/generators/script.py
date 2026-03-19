"""
Script Generator — generates short, viral YouTube Shorts / Instagram Reels scripts
using Gemini AI with few-shot examples and automatic key rotation.
"""
import os
import random
import google.generativeai as genai

# ---------------------------------------------------------------------------
# API key management — supports multiple keys (comma-separated)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Few-shot examples — teach the model what "good" looks like
# ---------------------------------------------------------------------------
EXAMPLE_SCRIPTS = [
    {
        "topic": "best wireless earbuds 2026",
        "title": "NEVER BUY AIRPODS AGAIN!",
        "script": (
            "Stop wasting money on AirPods! I just tested the top three wireless earbuds "
            "of 2026 and Apple isn't even number one. The Soundcore Space A40 — sixty bucks, "
            "punchy bass, ten hours battery. Insane value. Second, Samsung Galaxy Buds 3. "
            "If you own an Android, these integrate perfectly without the Apple tax. "
            "But the king? The Nothing Ear. Transparent design, high-res audio, half "
            "the price of AirPods Pro. Check the link in bio for the full breakdown!"
        ),
    },
    {
        "topic": "AI tools that will replace your job",
        "title": "AI Is Coming For Your Job",
        "script": (
            "Five AI tools that are genuinely replacing real jobs right now. "
            "Number one: ChatGPT is already replacing junior copywriters — companies "
            "cut headcount by 30 percent. Number two: Midjourney killed stock photo sales "
            "overnight. Number three: GitHub Copilot is writing 40 percent of all new code. "
            "Number four: Perplexity is wrecking SEO blogging. Number five: Synthesia is "
            "replacing corporate video teams. Adapt or get left behind. "
            "Check the link in bio for the full breakdown!"
        ),
    },
]

# ---------------------------------------------------------------------------
# Fallback topics (used only if Gemini is completely unavailable)
# ---------------------------------------------------------------------------
FALLBACK_TOPICS = [
    "The $50 gadget that beats your laptop",
    "Hidden iPhone features nobody talks about",
    "This USB-C hub changes everything",
    "Stop buying expensive earbuds — here's why",
    "The smartwatch Apple doesn't want you to own",
    "AI tools that will replace your job in 2026",
    "The gaming mouse pros secretly use",
    "Mechanical keyboards are a luxury scam",
]


# ---------------------------------------------------------------------------
# Main script generation
# ---------------------------------------------------------------------------
def generate_script(topic: str, attempt: int = 1) -> str | None:
    """
    Generate a short viral script (100-130 words) for the given topic.

    Returns: raw response string from Gemini, or None on total failure.
    """
    print(f"🤖 Generating short viral script (attempt {attempt}/3)...")

    api_key = _next_key()
    if not api_key:
        print("❌ No Gemini API keys available. Set GEMINI_API_KEYS in your secrets.")
        return _build_fallback_script(topic)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        examples_text = "\n\n".join(
            f"Example:\nTopic: {ex['topic']}\nTitle: {ex['title']}\nScript: {ex['script']}"
            for ex in EXAMPLE_SCRIPTS
        )

        prompt = f"""You are an expert YouTube Shorts scriptwriter for the viral tech channel "Tech 8ytees".
Write SHORT, PUNCHY, VIRAL scripts that are exactly 110-130 WORDS.

STUDY THESE EXAMPLES (notice they are short ~120 words):
{examples_text}

---
TASK: Write a 110-130 word script about: "{topic}"

NON-NEGOTIABLE RULES:
1. WORD COUNT: exactly 110-130 words. Not 200, not 300. SHORT AND PUNCHY.
2. Start with a HOOK that grabs attention in the very first sentence.
3. Make 2-3 punchy points, each in 1-2 short sentences.
4. Use conversational language. Sound like a real human, not a robot.
5. End EXACTLY with: "Check the link in bio for the full breakdown!"
6. No emojis in the script text.

OUTPUT FORMAT (no extra text):
TITLE: [Clickbaity title under 60 chars, ALL CAPS words]
SCRIPT: [110-130 word punchy script]
TAGS: [10 comma-separated YouTube tags]
DESCRIPTION: [2-3 sentences for video description]
THUMBNAIL_TEXT: [2-4 words MAX, ALL CAPS]
"""
        response = model.generate_content(prompt)
        script_text = response.text.strip()

        # Validate word count
        if "SCRIPT:" in script_text:
            body = script_text.split("SCRIPT:")[1].split("TAGS:")[0].strip()
            wc = len(body.split())
            print(f"📝 Script word count: {wc} words")
            if wc < 80 or wc > 180:
                print(f"⚠️  Script is {wc} words (target: 110-130). Regenerating (attempt {attempt})...")
                if attempt < 3:
                    return generate_script(topic, attempt + 1)
                # Accept it on final attempt
                print("⚠️  Accepting script despite length — 3 attempts exhausted.")

        return script_text

    except Exception as e:
        err = str(e).lower()
        if "quota" in err or "resource_exhausted" in err:
            print(f"⚠️  Gemini key exhausted, rotating to next key...")
            if attempt <= len(GEMINI_KEYS):
                return generate_script(topic, attempt + 1)
        print(f"❌ Gemini API error: {e}")
        return _build_fallback_script(topic)


def _build_fallback_script(topic: str) -> str:
    """Return a template script when Gemini is unavailable."""
    print("⚠️  Using fallback script template (Gemini unavailable).")
    safe_topic = topic[:50]
    return f"""TITLE: {safe_topic[:55].upper()}
SCRIPT: Here's something nobody in tech is talking about. {safe_topic}. \
This has changed dramatically in 2026 and most people still don't know it. \
First, the technology has gotten significantly better. The options are more \
diverse and more affordable than ever before. Second, even budget options now \
include premium features that used to cost twice as much. Third, if you haven't \
looked at this in the last six months, you are missing out. The gap between \
cheap and expensive has never been smaller. This is genuinely the best time \
to make a decision. Check the link in bio for the full breakdown!
TAGS: tech, gadgets, review, 2026, shorts, techy, comparison, buying guide, recommendations, viral
DESCRIPTION: Everything you need to know about {safe_topic} in 2026. Drop your questions in the comments!
THUMBNAIL_TEXT: {safe_topic[:20].upper()}"""


# ---------------------------------------------------------------------------
# Script parsing
# ---------------------------------------------------------------------------
def parse_script(raw: str) -> dict | None:
    """Parse the Gemini response into a structured dict."""
    if not raw:
        return None

    fields = ["title", "script", "tags", "description", "thumbnail_text"]
    data = {f: "" for f in fields}
    current_key = None
    buffer = []

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
        words = data["title"].split()[:4]
        data["thumbnail_text"] = " ".join(words).upper()

    script_words = len(data["script"].split())
    title = data["title"] or "(no title)"
    print(f"✅ Script parsed — Title: {title} ({script_words} words)")

    return data
