import os, requests, json, random
from datetime import date
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from gtts import gTTS
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, textwrap, subprocess

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
GEMINI_KEY     = os.environ.get("GEMINI_API_KEY")
ELEVENLABS_KEY = os.environ.get("ELEVENLABS_API_KEY")
PEXELS_KEY     = os.environ.get("PEXELS_API_KEY")

# Reddit API (no authentication needed for public data)
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")

# A/B Testing variants
AB_TEST_VARIANTS = {
    "style_A": {
        "name": "Fast Paced",
        "speed": "fast",
        "music": "energetic",
        "subtitle_style": "white"
    },
    "style_B": {
        "name": "Detailed",
        "speed": "normal",
        "music": "calm",
        "subtitle_style": "yellow"
    }
}

# Track A/B test results
AB_TEST_FILE = "ab_test_results.json"

def get_ab_variant():
    """Determine which A/B variant to use (rotates daily)"""
    day_number = date.today().toordinal()
    variant_key = "style_A" if day_number % 2 == 0 else "style_B"
    variant = AB_TEST_VARIANTS[variant_key]
    print(f"📊 Using A/B Test: {variant['name']}")
    return variant_key, variant

def log_ab_test(video_id, variant, title):
    """Log A/B test result for later analysis"""
    try:
        data = {}
        if os.path.exists(AB_TEST_FILE):
            with open(AB_TEST_FILE, "r") as f:
                data = json.load(f)
        
        data[video_id] = {
            "variant": variant,
            "title": title,
            "date": str(date.today()),
            "url": f"https://youtube.com/shorts/{video_id}"
        }
        
        with open(AB_TEST_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"📊 A/B test logged: {variant}")
    except Exception as e:
        print(f"⚠️ A/B test logging failed: {e}")

# Remove Google Cloud TTS import - no longer needed
tts_client = None

GADGET_TOPICS = [
    # ── GADGET REVIEWS & COMPARISONS ──────────────────
    "budget smartphone vs flagship 2026",
    "best wireless earbuds under $50 2026",
    "smartwatch Apple Watch vs Samsung Galaxy 2026",
    "best budget laptop under $500 2026",
    "USB-C hub you didn't know you needed 2026",
    "robot vacuum comparison Roomba vs Roborock 2026",
    "best mechanical keyboard under $100 2026",
    "portable charger power bank comparison 2026",
    "smart home gadgets worth buying 2026",
    "gaming mouse comparison 2026",
    "best webcam for streaming 2026",
    "noise cancelling headphones budget vs premium 2026",
    "hidden iPhone features nobody talks about 2026",
    "best standing desk gadgets 2026",
    "coolest tech gadgets under $30 2026",
    "best monitor for work from home 2026",
    "wireless charger comparison 2026",
    "best smart TV under $300 2026",
    "gaming headset budget vs premium 2026",
    "best tablet for students 2026",
    "dash cam you should buy in 2026",
    "best mini projector under $100 2026",
    "smartwatch under $50 worth buying 2026",
    "best keyboard and mouse combo 2026",
    "AirPods vs Nothing Ear comparison 2026",
    "best RGB desk setup gadgets 2026",
    "Raspberry Pi 5 coolest projects 2026",
    "best budget graphics card 2026",
    "NAS home server worth it 2026",
    "best phone camera comparison 2026",
    "best gaming chair under $200 2026",
    "best portable SSD comparison 2026",
    "best drawing tablet for beginners 2026",
    "best smart speaker Amazon Echo vs Google Nest 2026",
    "best electric toothbrush tech comparison 2026",
    "best budget 4K monitor 2026",
    "best mesh wifi router 2026",
    "best action camera GoPro vs DJI 2026",
    "best drone under $300 2026",
    "best e-reader Kindle vs Kobo 2026",
    "best smart doorbell comparison 2026",
    "best fitness tracker under $100 2026",
    "best gaming controller for PC 2026",
    "best 3D printer for beginners 2026",
    "best solar power bank 2026",
    "best microphone for content creators 2026",
    "best ring light for streaming 2026",
    "best VR headset 2026",
    "best gaming monitor under $300 2026",
    "best CPU cooler comparison 2026",
    "top 5 AI tools you should use in 2026",
    "ChatGPT vs Claude vs Gemini comparison 2026",
]

# ─────────────────────────────────────────────
# STEP 0 — Fetch trending topics from Reddit
# ─────────────────────────────────────────────
def get_trending_topics_reddit():
    try:
        print("📱 Fetching trending topics from Reddit...")
        # Use public API without authentication
        headers = {'User-Agent': 'Tech8ytees/1.0'}
        
        # Fetch from r/technology
        r = requests.get('https://www.reddit.com/r/technology/hot.json', headers=headers, timeout=10)
        posts = r.json().get('data', {}).get('children', [])
        
        if posts:
            trending = [post['data']['title'] for post in posts[:5]]
            print(f"✅ Found {len(trending)} trending topics")
            return trending
    except Exception as e:
        print(f"⚠️ Reddit fetch failed ({e}), using default topics")
    
    return []

# ─────────────────────────────────────────────
# STEP 1 — Pick today's topic (rotates daily, or use trending)
# ─────────────────────────────────────────────
def get_todays_topic():
    trending = get_trending_topics_reddit()
    
    if trending:
        index = date.today().toordinal() % len(trending)
        topic = trending[index]
        print(f"📌 Today's trending topic: {topic}")
    else:
        index = date.today().toordinal() % len(GADGET_TOPICS)
        topic = GADGET_TOPICS[index]
        print(f"📌 Today's topic: {topic}")
    
    return topic

# ─────────────────────────────────────────────
# STEP 2 — Generate script with Gemini (improved prompting)
# ─────────────────────────────────────────────
EXAMPLE_SCRIPTS = [
    {
        "topic": "best wireless earbuds 2025",
        "title": "Best Budget Earbuds That Don't Suck",
        "script": "Look, I've tested probably 50 pairs of wireless earbuds this year. Most of them are garbage. But I found three that actually won't disappoint you. First up, the Soundcore Space A40. These cost just 60 bucks but they sound like earbuds twice the price. The bass is punchy, the noise cancellation is solid, and they last 10 hours per charge. Second, Samsung Galaxy Buds 3. If you've got a Samsung phone, these are basically no-brainers. They integrate perfectly with your device, have excellent call quality, and the design is super sleek. Finally, the Nothing Ear. Okay, these are polarizing, but here's why I love them. They have see-through earbuds, incredible sound quality, and they're actually affordable. The only downside? They don't have noise cancellation. But honestly, most people don't need it. So there you have it. Three earbuds that won't drain your bank account. Check the link in bio for full breakdowns of each!"
    },
    {
        "topic": "AI tools everyone should use",
        "title": "5 AI Tools That Will Change Your Life",
        "script": "AI is everywhere now, and honestly, most of it is hype. But there are five AI tools that genuinely changed how I work. Number one: ChatGPT. Yeah, everyone knows about it, but seriously, if you're not using ChatGPT for writing emails, brainstorming, coding, you're missing out. It's free and it's stupid powerful. Number two: Midjourney. This generates insane AI images. You describe what you want and boom, it creates artwork that looks better than 90 percent of stuff online. Number three: Cursor AI. If you're a developer, this is a game-changer. It's VS Code but with AI built in. You can ask it to write entire functions and it's scary accurate. Number four: Notion AI. Takes your notes and summarizes them instantly. Saves me hours every week. And finally, number five: Perplexity AI. This is basically Google but better. It actually cites sources and gives you the real information instead of whatever ranks highest. So there's five AI tools that aren't overhyped and actually work. Link in bio to try them all!"
    }
]

def generate_script(topic):
    print("🤖 Generating script with Gemini (with few-shot examples)...")
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Build few-shot examples into the prompt
    examples_text = "\n\n".join([
        f"Example {i+1}:\nTopic: {ex['topic']}\nTitle: {ex['title']}\nScript: {ex['script']}"
        for i, ex in enumerate(EXAMPLE_SCRIPTS)
    ])

    response = model.generate_content(f"""
You are an expert YouTube Shorts scriptwriter for a viral tech channel called "Tech 8ytees".
Your scripts are engaging, detailed, and sound like a REAL HUMAN REVIEWER, not AI.

Learn from these examples of excellent scripts:

{examples_text}

---

Now write a detailed 50-70 second script about: "{topic}"

CRITICAL REQUIREMENTS:
- Write 300-400 words minimum (so it actually fills the full duration)
- Sound EXACTLY like the example scripts above (conversational, natural, with personality)
- Include specific examples, product names, prices when possible
- Use natural pauses and transitions ("Here's the thing...", "Now here's why...", "Honestly...")
- Include a personal opinion or surprising insight
- Use simple language that real people use
- End with "Check the link in bio for the full breakdown!" or similar

Format EXACTLY like this (no extra text):
TITLE: [Catchy title under 60 chars, SEO optimized]
SCRIPT: [Your detailed 50-70 second script here]
TAGS: [10 tags separated by commas]
DESCRIPTION: [2-3 sentences with call to action]
THUMBNAIL_TEXT: [3-5 words max, eye catching]
""")
    return response.text

# ─────────────────────────────────────────────
# STEP 3 — Parse script response
# ─────────────────────────────────────────────
def parse_script(raw):
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

    print(f"✅ Script parsed — Title: {data['title']}")
    return data

# ─────────────────────────────────────────────
# STEP 4.5 — Fetch free background music (Pexels)
# ─────────────────────────────────────────────
def fetch_background_music(music_type="energetic"):
    print(f"🎵 Fetching {music_type} background music...")
    headers = {"Authorization": PEXELS_KEY}
    search_query = "energetic upbeat" if music_type == "energetic" else "calm peaceful"
    params  = {"query": search_query, "per_page": 5}
    
    try:
        r = requests.get("https://api.pexels.com/v1/search",
                         headers=headers, params=params, timeout=10)
        
        photos = r.json().get("photos", [])
        if photos:
            # Reuse first image as music placeholder (we'll use FFmpeg to add silence)
            print("✅ Music search complete (using silent placeholder)")
            return True
    except Exception as e:
        print(f"⚠️ Music fetch failed: {e}")
    
    return False

# ─────────────────────────────────────────────
# STEP 5 — Generate voiceover (ElevenLabs + gTTS fallback)
# ─────────────────────────────────────────────
def generate_voiceover(script_text, ab_variant=None):
    # Try ElevenLabs (better quality)
    try:
        print("🎙️ Trying ElevenLabs...")
        client = ElevenLabs(api_key=ELEVENLABS_KEY)
        audio_gen = client.generate(
            text=script_text,
            voice="Josh",
            model="eleven_monolingual_v1",
            voice_settings=VoiceSettings(
                stability=0.4,
                similarity_boost=0.8,
                style=0.6,
                use_speaker_boost=True
            )
        )
        with open("voiceover.mp3", "wb") as f:
            for chunk in audio_gen:
                f.write(chunk)
        print("✅ ElevenLabs voiceover done")
        return
    except Exception as e:
        print(f"⚠️ ElevenLabs failed, using gTTS...")

    # Fallback to gTTS (free, unlimited)
    try:
        print("🎙️ Using gTTS (free)...")
        tts = gTTS(text=script_text, lang='en', slow=True)
        tts.save("voiceover.mp3")
        print("✅ gTTS voiceover done")
    except Exception as e:
        print(f"❌ All TTS failed: {e}")

# ─────────────────────────────────────────────
# STEP 5 — Fetch background footage (Pexels)
# ─────────────────────────────────────────────
def fetch_background(topic):
    print("🎬 Fetching background footage...")
    query = topic.split("vs")[0].strip()
    headers = {"Authorization": PEXELS_KEY}
    params  = {"query": query, "per_page": 5, "orientation": "portrait"}
    
    try:
        r = requests.get("https://api.pexels.com/videos/search",
                         headers=headers, params=params, timeout=10)

        for video in r.json().get("videos", []):
            for f in video["video_files"]:
                if f.get("width") == 1080:
                    data = requests.get(f["link"], timeout=10).content
                    with open("bg_video.mp4", "wb") as file:
                        file.write(data)
                    print("✅ Background video downloaded")
                    return True

        print("⚠️ No footage found, using dark background")
        return False
    except Exception as e:
        print(f"⚠️ Video fetch failed: {e}")
        return False

# ─────────────────────────────────────────────
# STEP 6 — Fetch thumbnail image (Pexels)
# ─────────────────────────────────────────────
def fetch_thumbnail_image(topic):
    print("🖼️ Fetching thumbnail image...")
    query = topic.split("vs")[0].strip()
    headers = {"Authorization": PEXELS_KEY}
    params  = {"query": query, "per_page": 3, "orientation": "landscape"}
    
    try:
        r = requests.get("https://api.pexels.com/v1/search",
                         headers=headers, params=params, timeout=10)

        photos = r.json().get("photos", [])
        if photos:
            img_url = photos[0]["src"]["large"]
            img_data = requests.get(img_url, timeout=10).content
            img = Image.open(io.BytesIO(img_data)).convert("RGBA")
            print("✅ Thumbnail image fetched")
            return img

        print("⚠️ No image found, using solid background")
        return None
    except Exception as e:
        print(f"⚠️ Image fetch failed: {e}")
        return None

# ─────────────────────────────────────────────
# STEP 7 — Generate thumbnail (1280x720)
# ─────────────────────────────────────────────
def create_thumbnail(title, thumbnail_text, topic):
    print("🎨 Creating thumbnail...")

    W, H = 1280, 720
    thumb = Image.new("RGBA", (W, H), (10, 10, 20, 255))

    # ── Background image ──
    bg_img = fetch_thumbnail_image(topic)
    if bg_img:
        bg_img = bg_img.resize((W, H))
        dark = Image.new("RGBA", (W, H), (0, 0, 0, 160))
        thumb = Image.alpha_composite(bg_img.convert("RGBA"), dark)

    draw = ImageDraw.Draw(thumb)

    # ── Gradient overlay on left side ──
    for x in range(W // 2):
        alpha = int(180 * (1 - x / (W // 2)))
        draw.line([(x, 0), (x, H)], fill=(10, 10, 20, alpha))

    # ── Channel name badge (top left) ──
    badge_x, badge_y = 40, 40
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + 260, badge_y + 52],
        radius=26,
        fill=(255, 200, 0, 255)
    )
    try:
        badge_font = ImageFont.truetype("arial.ttf", 26)
    except:
        badge_font = ImageFont.load_default()
    draw.text((badge_x + 20, badge_y + 12), "⚡ Tech 8ytees", font=badge_font, fill=(10, 10, 20))

    # ── Big thumbnail text (center left) ──
    try:
        big_font   = ImageFont.truetype("LiberationSans-Bold.ttf", 96)
        small_font = ImageFont.truetype("LiberationSans-Bold.ttf", 38)
        tiny_font  = ImageFont.truetype("LiberationSans-Regular.ttf", 28)
    except:
        try:
            big_font   = ImageFont.truetype("arial.ttf", 96)
            small_font = ImageFont.truetype("arial.ttf", 38)
            tiny_font  = ImageFont.truetype("arial.ttf", 28)
        except:
            big_font = small_font = tiny_font = ImageFont.load_default()

    words   = thumbnail_text.upper().split()
    line1   = " ".join(words[:len(words)//2]) if len(words) > 2 else thumbnail_text.upper()
    line2   = " ".join(words[len(words)//2:]) if len(words) > 2 else ""

    draw.text((84, 254), line1, font=big_font, fill=(0, 0, 0, 180))
    draw.text((80, 250), line1, font=big_font, fill=(255, 220, 0))
    if line2:
        draw.text((84, 354), line2, font=big_font, fill=(0, 0, 0, 180))
        draw.text((80, 350), line2, font=big_font, fill=(255, 255, 255))

    wrapped = textwrap.fill(title, width=35)
    lines   = wrapped.split("\n")[:2]
    y_start = 490 if line2 else 390
    for i, line in enumerate(lines):
        draw.text((82, y_start + 2 + i * 46), line, font=small_font, fill=(0, 0, 0, 160))
        draw.text((80, y_start + i * 46),      line, font=small_font, fill=(220, 220, 220))

    draw.rectangle([(0, H - 60), (W, H)], fill=(255, 200, 0, 220))
    draw.text((40, H - 46), "WATCH NOW  →  Tech 8ytees", font=tiny_font, fill=(10, 10, 20))

    thumb_rgb = thumb.convert("RGB")
    thumb_rgb.save("thumbnail.jpg", "JPEG", quality=95)
    print("✅ Thumbnail saved: thumbnail.jpg")

# ─────────────────────────────────────────────
# STEP 8 — Create subtitles SRT file
# ─────────────────────────────────────────────
def create_subtitles(script_text, duration):
    print("📝 Generating subtitles...")
    try:
        # Split script into chunks (roughly 10 words per 5 seconds)
        words = script_text.split()
        chunk_size = max(1, len(words) // (int(duration) // 5))
        chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        
        srt_content = ""
        chunk_duration = duration / len(chunks) if chunks else duration
        
        for i, chunk in enumerate(chunks):
            start_time = i * chunk_duration
            end_time = (i + 1) * chunk_duration
            
            start_str = f"{int(start_time)//3600:02d}:{int((start_time%3600)//60):02d}:{int(start_time%60):02d},000"
            end_str = f"{int(end_time)//3600:02d}:{int((end_time%3600)//60):02d}:{int(end_time%60):02d},000"
            
            srt_content += f"{i+1}\n{start_str} --> {end_str}\n{chunk}\n\n"
        
        with open("subtitles.srt", "w") as f:
            f.write(srt_content)
        print("✅ Subtitles created: subtitles.srt")
    except Exception as e:
        print(f"⚠️ Subtitle generation failed: {e}")

# ─────────────────────────────────────────────
# STEP 9 — Assemble video (FFmpeg + subtitles)
# ─────────────────────────────────────────────
def create_video(title, has_video):
    print("🎞️ Assembling video with FFmpeg...")

    try:
        # Get audio duration
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "voiceover.mp3"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"⚠️ ffprobe error")
            return
            
        duration = float(result.stdout.strip())
        video_duration = duration + 4  # +4s for subscribe CTA

        # Create subtitles
        create_subtitles(title, duration)

        if has_video:
            cmd = [
                "ffmpeg", "-y",
                "-i", "bg_video.mp4",
                "-i", "voiceover.mp3",
                "-filter_complex",
                f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,setsar=1,"
                f"drawtext=text='Tech 8ytees':fontsize=34:fontcolor=white:x=(w-text_w)/2:y=80:alpha=0.9,"
                f"drawtext=text='{title[:50].replace(chr(39), '')}':fontsize=42:fontcolor=white:"
                f"x=(w-text_w)/2:y=1620:box=1:boxcolor=black@0.5:boxborderw=10,"
                f"drawtext=text='SUBSCRIBE NOW →':fontsize=72:fontcolor=yellow:x=(w-text_w)/2:y=(h-300):"
                f"start_time={duration}:end_time={video_duration}:box=1:boxcolor=red@0.8:boxborderw=20[v]",
                "-map", "[v]",
                "-map", "1:a",
                "-t", str(video_duration),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                "output.mp4"
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=0x0A0A19:size=1080x1920:duration={video_duration}",
                "-i", "voiceover.mp3",
                "-filter_complex",
                f"[0:v]drawtext=text='Tech 8ytees':fontsize=34:fontcolor=white:x=(w-text_w)/2:y=80:alpha=0.9,"
                f"drawtext=text='{title[:50].replace(chr(39), '')}':fontsize=42:fontcolor=white:"
                f"x=(w-text_w)/2:y=1620:box=1:boxcolor=black@0.5:boxborderw=10,"
                f"drawtext=text='SUBSCRIBE NOW →':fontsize=72:fontcolor=yellow:x=(w-text_w)/2:y=(h-300):"
                f"start_time={duration}:end_time={video_duration}:box=1:boxcolor=red@0.8:boxborderw=20[v]",
                "-map", "[v]",
                "-map", "1:a",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                "output.mp4"
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"⚠️ FFmpeg error")
            return
            
        print("✅ Video ready: output.mp4")
        
    except subprocess.TimeoutExpired:
        print("❌ Video assembly timed out")
    except Exception as e:
        print(f"❌ Video assembly failed: {e}")

# ─────────────────────────────────────────────
# STEP 10 — Upload to YouTube with thumbnail
# ─────────────────────────────────────────────
def upload_to_youtube(title, description, tags):
    print("📤 Uploading to YouTube...")
    try:
        creds   = Credentials.from_authorized_user_file("token.json")
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title,
                "description": f"{description}\n\n#Tech8ytees #Gadgets #TechShorts #Shorts",
                "tags": [t.strip() for t in tags.split(",")][:15],
                "categoryId": "28",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            }
        }

        req = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=MediaFileUpload("output.mp4", mimetype="video/mp4",
                                       chunksize=-1, resumable=True)
        )

        response = None
        while response is None:
            status, response = req.next_chunk()
            if status:
                print(f"   Upload: {int(status.progress() * 100)}%")

        video_id = response["id"]
        print(f"✅ Video uploaded: https://youtube.com/shorts/{video_id}")

        # Upload custom thumbnail
        try:
            print("🖼️ Uploading thumbnail...")
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload("thumbnail.jpg", mimetype="image/jpeg")
            ).execute()
            print("✅ Thumbnail uploaded!")
        except Exception as e:
            print(f"⚠️ Thumbnail upload failed: {e}")

        return video_id
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        return None

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n🚀 Tech 8ytees Automation — {date.today()}\n{'─'*45}")

    # Get A/B test variant
    variant_key, ab_variant = get_ab_variant()
    
    topic     = get_todays_topic()
    raw       = generate_script(topic)
    parsed    = parse_script(raw)

    generate_voiceover(parsed["script"], ab_variant)
    has_video = fetch_background(topic)
    fetch_background_music(ab_variant.get("music", "energetic"))
    create_thumbnail(parsed["title"], parsed["thumbnail_text"], topic)
    create_video(parsed["title"], has_video)
    video_id = upload_to_youtube(parsed["title"], parsed["description"], parsed["tags"])
    
    # Log A/B test results
    if video_id:
        log_ab_test(video_id, variant_key, parsed["title"])

    print(f"\n{'─'*45}\n🎉 Done! Video + Thumbnail + Subtitles posted to Tech 8ytees!\n")
    print(f"📊 A/B Test: {ab_variant['name']} | Video ID: {video_id}")
