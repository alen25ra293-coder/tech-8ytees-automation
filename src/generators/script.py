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
        "title": "NEVER BUY AIRPODS AGAIN!",
        "script": "Stop wasting your money on AirPods! I just tested the top three wireless earbuds of 2026, and Apple isn't even number one anymore. First up, the Soundcore Space A40. For sixty bucks, you get punchy bass and ten hours of battery life—literally insane value. Second, the Samsung Galaxy Buds 3. If you own an Android, these look sleeker and integrate perfectly without the Apple tax. But the absolute king? The Nothing Ear. These completely transparent earbuds look like they're from the future, pack incredible high-res audio, and cost half as much as the AirPods Pro. Check the link in my bio for the full list before you waste your cash!"
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
You are an expert YouTube Shorts and TikTok scriptwriter for a viral tech channel called "Tech 8ytees".
Your scripts are aggressive, highly engaging, and sound like a REAL HUMAN TECH CREATOR out to expose the truth.

Learn from this example of an excellent, perfectly-paced viral script:
{examples_text}

---
CRITICAL: Write a highly engaging, controversial, and punchy script about: "{topic}"

ABSOLUTE REQUIREMENTS (DO NOT SKIP):
- The script MUST be EXACTLY 100-130 words. This guarantees the 40-50 second algorithm sweet spot.
- The FIRST sentence MUST be a controversial or massive hook (e.g., "Stop buying X", "You've been lied to about Y", "This gadget is illegal"). This is CRITICAL for the 3-second retention!
- Keep it extremely fast-paced. Cut all boring intro fluff.
- End with: "Check the link in bio for the full breakdown!"
- The TITLE MUST be extremely clickbaity but accurate.
- THUMBNAIL_TEXT MUST be 2-4 words MAX and ALL CAPS (e.g., "APPLE LIED?!", "DO NOT BUY!").
- The output MUST follow this exact format below and contain NO OTHER TEXT.

Format EXACTLY like this (no extra text):
TITLE: [Catchy title under 60 chars]
SCRIPT: [100-130 word script]
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
            
            if word_count < 80 or word_count > 160:
                print(f"⚠️ Script length is {word_count} words (target 100-130). Regenerating...")
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
