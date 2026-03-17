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
    print(f"🤖 Generating short viral script (attempt {attempt}/3)...")
    
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
You are an expert YouTube Shorts scriptwriter for a viral tech channel "Tech 8ytees".
Your job is to write SHORT, PUNCHY, VIRAL scripts that are 100-130 WORDS ONLY.
This is NOT a long-form essay. This is a SHORT viral video script.

STUDY THIS EXAMPLE (notice it's SHORT, around 100 words):
{examples_text}

---
TASK: Write a 100-130 word script about: "{topic}"

ABSOLUTE NON-NEGOTIABLE REQUIREMENTS:
1. WORD COUNT MUST BE 100-130 WORDS. NOT 200. NOT 300. NOT 500. EXACTLY 100-130 WORDS.
2. Start with a CONTROVERSIAL HOOK that grabs attention in 1 second.
3. Get straight to the point. NO long introductions.
4. Make 2-3 key points, each 1-2 sentences.
5. End with "Check the link in bio for the full breakdown!"
6. The entire script must be readable in 40-50 seconds when spoken at normal speed.

OUTPUT FORMAT (NO EXTRA TEXT):
TITLE: [Catchy, clickbaity title under 60 chars]
SCRIPT: [EXACTLY 100-130 words - SHORT and punchy]
TAGS: [10 comma-separated tags]
DESCRIPTION: [2-3 sentences]
THUMBNAIL_TEXT: [2-4 words MAX, ALL CAPS]
"""
        response = model.generate_content(prompt)
        script_text = response.text
        
        # Validate script length - STRICT enforcement
        if "SCRIPT:" in script_text:
            script_content = script_text.split("SCRIPT:")[1].split("TAGS:")[0].strip()
            word_count = len(script_content.split())
            print(f"📝 Script word count: {word_count} words")
            
            if word_count < 80 or word_count > 160:
                print(f"⚠️ Script is {word_count} words (need 100-130). Regenerating attempt {attempt}...")
                if attempt < 3:
                    return generate_script(topic, attempt + 1)
                else:
                    print(f"❌ Failed to generate correct length after {attempt} attempts. Returning anyway.")
        
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
