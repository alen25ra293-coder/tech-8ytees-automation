import os
import google.generativeai as genai

gemini_keys_env = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
GEMINI_KEYS = [k.strip() for k in gemini_keys_env.split(",") if k.strip()]
CURRENT_KEY_INDEX = 0

def get_next_gemini_key():
    global CURRENT_KEY_INDEX
    if not GEMINI_KEYS:
        return None
    key = GEMINI_KEYS[CURRENT_KEY_INDEX]
    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GEMINI_KEYS)
    return key

EXAMPLE_SCRIPTS = [
    {
        "topic": "best wireless earbuds 2026",
        "title": "Top 3 Wireless Earbuds of 2026 You MUST See",
        "script": "If you're still using your old wired headphones or those cheap knockoffs from three years ago, you're missing out. Get this, 2026 has completely changed the game for wireless earbuds. I have tested over thirty different pairs this year alone, and most of them are honestly garbage, but I finally found the absolute top three that are actually worth your money. First up on the list, the Soundcore Space A40. These are coming in at just sixty bucks, but they sound like earbuds that cost twice as much. The bass is super punchy, the active noise cancellation is surprisingly solid, and they last a massive ten hours on a single charge. Second on the list, we have the Samsung Galaxy Buds 3. Now, if you already have a Samsung phone, these are a complete no-brainer. They integrate perfectly with your device ecosystem, have excellent microphone quality for calls, and the design is incredibly sleek and comfortable in the ear. Finally, the Nothing Ear. Okay, these are definitely polarizing, but here is exactly why I love them. They have those transparent, see-through earbuds that look like nothing else on the market, incredible high-resolution sound quality, and they are genuinely affordable for what you get. The only downside is they don't have noise cancellation, but honestly, with the passive seal, most people don't even need it. So there you have it, three incredible wireless earbuds that absolutely won't drain your bank account but will upgrade your audio game. Which pair would you choose? Let me know, and check the link in the bio for a full breakdown of each!"
    }
]

def generate_script(topic, attempt=1):
    print("🤖 Generating long-form script with Gemini...")
    
    api_key = get_next_gemini_key()
    if not api_key:
        print("❌ No Gemini API keys available.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        examples_text = "\n\n".join([
            f"Example:\nTopic: {ex['topic']}\nTitle: {ex['title']}\nScript: {ex['script']}"
            for ex in EXAMPLE_SCRIPTS
        ])

        prompt = f"""
You are an expert YouTube Shorts scriptwriter for a viral tech channel called "Tech 8ytees".
Your scripts are engaging, detailed, and sound like a REAL HUMAN REVIEWER, not AI.

Learn from this example of an excellent, LONG script:
{examples_text}

---
CRITICAL: Write a HIGHLY DETAILED, LONG script about: "{topic}"

ABSOLUTE REQUIREMENTS (DO NOT SKIP):
- The script MUST be 350-500 words minimum. This is CRITICAL because the video MUST be over 45-60 seconds when spoken extremely fast!
- Provide a Top 3 list or a highly detailed comparison to bulk out the word count naturally.
- Use transitions like: "Here's the thing...", "Now here's the crazy part...", "Honestly...", "Get this..."
- End with: "Check the link in bio for the full breakdown!"
- The output MUST follow this exact format below and contain NO OTHER TEXT.

Format EXACTLY like this (no extra text):
TITLE: [Catchy title under 60 chars]
SCRIPT: [LONG 350+ word script]
TAGS: [10 comma separated tags]
DESCRIPTION: [2-3 sentences]
THUMBNAIL_TEXT: [3-5 words max]
"""
        response = model.generate_content(prompt)
        script_text = response.text
        
        # Validate script length
        if "SCRIPT:" in script_text:
            script_content = script_text.split("SCRIPT:")[1].split("TAGS:")[0].strip()
            word_count = len(script_content.split())
            print(f"📝 Script word count: {word_count} words")
            
            if word_count < 200:
                print(f"⚠️ Script is too short ({word_count} words). Need at least 200. Regenerating...")
                if attempt < 3:
                    return generate_script(topic, attempt + 1)
        
        return script_text
        
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "resource_exhausted" in error_msg.lower():
            if attempt < len(GEMINI_KEYS):
                return generate_script(topic, attempt + 1)
        print(f"❌ Gemini API error: {error_msg}")
        return None

def parse_script(raw):
    if not raw:
        return None
        
    data = {
        "title": "",
        "script": "",
        "tags": "",
        "description": "",
        "thumbnail_text": ""
    }
    current_key = None
    buffer = []

    for line in raw.strip().split("\n"):
        matched = False
        for key in data:
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

    if not data["thumbnail_text"]:
        data["thumbnail_text"] = data["title"][:30]

    return data
