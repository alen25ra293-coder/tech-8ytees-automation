import os, requests
from datetime import date
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from gtts import gTTS
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, textwrap

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
GEMINI_KEY     = os.environ["GEMINI_API_KEY"]
ELEVENLABS_KEY = os.environ["ELEVENLABS_API_KEY"]
PEXELS_KEY     = os.environ["PEXELS_API_KEY"]

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

    # ── AI TOOLS & NEWS ────────────────────────────────
    "top 5 AI tools you should use in 2026",
    "ChatGPT vs Claude vs Gemini comparison 2026",
    "best free AI image generators 2026",
    "AI tools that will replace your apps 2026",
    "how to use Claude AI to save hours daily 2026",
    "best AI video generators 2026",
    "AI tools for students that are totally free 2026",
    "Midjourney vs DALL-E vs Stable Diffusion 2026",
    "best AI writing tools 2026",
    "how to make money with AI tools in 2026",
    "AI tools for YouTube creators 2026",
    "best AI coding assistants for developers 2026",
    "top AI productivity tools 2026",
    "AI music generators you should try 2026",
    "best AI photo editors 2026",
    "how to use Gemini AI on Android 2026",
    "ChatGPT hidden features nobody uses 2026",
    "best AI voice cloning tools 2026",
    "AI tools that replace Photoshop for free 2026",
    "top 5 AI Chrome extensions 2026",
    "best AI presentation makers 2026",
    "AI tools for social media automation 2026",
    "how to build AI apps with no code 2026",
    "best AI note taking apps 2026",
    "top AI search engines replacing Google 2026",
    "best AI video editing tools 2026",
    "how to use AI to build a website for free 2026",
    "AI tools for graphic designers 2026",
    "best local AI models you can run on your PC 2026",
    "best AI chatbots comparison 2026",
    "AI tools for freelancers to earn more 2026",
    "best AI translation tools 2026",
    "best AI tools for video thumbnails 2026",
    "best AI resume builders 2026",
    "how to automate your business with AI 2026",
    "best AI meeting summarizers 2026",
    "best AI logo makers 2026",
    "how to use Copilot AI in Windows 2026",
    "best AI email writers 2026",
    "AI tools every entrepreneur should use 2026",

    # ── TECH TIPS & TRICKS ────────────────────────────
    "Windows 11 hidden features you should enable 2026",
    "Android settings you should turn on right now 2026",
    "best free software every PC user needs 2026",
    "how to speed up your old laptop for free 2026",
    "5 Google tricks nobody knows about 2026",
    "best VS Code extensions for developers 2026",
    "how to protect your privacy online 2026",
    "VPN worth it or waste of money 2026",
    "best browser in 2026 Chrome vs Firefox vs Brave",
    "cloud storage comparison Google vs iCloud vs OneDrive 2026",
    "how to set up dual monitors for productivity 2026",
    "best keyboard shortcuts everyone should know 2026",
    "how to clean your PC for better performance 2026",
    "best free antivirus software 2026",
    "how to backup your data properly 2026",
    "best password managers 2026",
    "how to make your WiFi faster 2026",
    "best Linux distro for beginners 2026",
    "how to remove bloatware from Windows 2026",
    "best free video editing software 2026",

    # ── SMARTPHONE TIPS ───────────────────────────────
    "hidden Android features you never knew existed 2026",
    "iPhone tips and tricks 2026",
    "how to extend your phone battery life 2026",
    "best Android apps you should install 2026",
    "best iPhone apps you are missing out on 2026",
    "how to transfer data to new phone 2026",
    "how to fix a slow Android phone 2026",
    "best Google Pixel tips and tricks 2026",
    "Samsung Galaxy hidden features 2026",

    # ── GAMING TECH ───────────────────────────────────
    "PS5 vs Xbox Series X which is better 2026",
    "best gaming laptop under $1000 2026",
    "PC gaming vs console gaming 2026",
    "best budget gaming PC build 2026",
    "best cloud gaming services 2026",
    "how to improve FPS in any PC game 2026",
    "Steam Deck worth buying 2026",
    "best free PC games you should play 2026",
]

# ─────────────────────────────────────────────
# STEP 1 — Pick today's topic
# ─────────────────────────────────────────────
def get_todays_topic():
    index = date.today().toordinal() % len(GADGET_TOPICS)
    topic = GADGET_TOPICS[index]
    print(f"📌 Today's topic: {topic}")
    return topic

# ─────────────────────────────────────────────
# STEP 2 — Generate script with Gemini
# ─────────────────────────────────────────────
def generate_script(topic):
    print("🤖 Generating script with Gemini...")
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    response = model.generate_content(f"""
You are an expert YouTube Shorts scriptwriter for a viral tech channel called "Tech 8ytees".
Your scripts are engaging, detailed, and always EXACTLY 50-70 seconds when spoken at normal pace.

Write a detailed 50-70 second script about: "{topic}"

IMPORTANT: 
- Write AT LEAST 300-400 words so it fills the full duration
- Include specific examples, numbers, and detailed explanations
- Use natural, conversational language (sounds like a real person talking)
- Include interesting facts or surprising insights
- Build curiosity and urgency throughout
- End with a strong call-to-action

Format EXACTLY like this (no extra text):
TITLE: [Catchy title under 60 chars, SEO optimized]
SCRIPT: [Detailed 50-70 second script with specific examples and facts]
TAGS: [10 tags separated by commas]
DESCRIPTION: [2-3 sentences with call to action]
THUMBNAIL_TEXT: [3-5 words max, big bold text for thumbnail, eye catching]

Rules:
- Hook in first 5 seconds with a surprising fact or question
- Simple words, conversational tone, natural pauses
- Include specific product names, prices, or examples
- Use transitions like "Here's the thing..." or "Now here's the crazy part..."
- End with "Check out the link in bio for the full breakdown!"
- Sound like a real tech reviewer with personality, NOT like AI
""")
    return response.text

# ─────────────────────────────────────────────
# STEP 3 — Parse Gemini's response
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

    # Fallback thumbnail text
    if not data["thumbnail_text"]:
        data["thumbnail_text"] = data["title"][:30]

    print(f"✅ Script parsed — Title: {data['title']}")
    return data

# ─────────────────────────────────────────────
# STEP 4 — Generate voiceover
# ─────────────────────────────────────────────
def generate_voiceover(script_text):
    # Try ElevenLabs first (better quality)
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

    # Fallback to gTTS (free, unlimited)
    except Exception as e:
        print(f"⚠️ ElevenLabs failed ({e}), using gTTS...")
        tts = gTTS(text=script_text, lang='en', slow=True)
        tts.save("voiceover.mp3")
        print("✅ gTTS voiceover done")

# ─────────────────────────────────────────────
# STEP 5 — Fetch background footage
# ─────────────────────────────────────────────
def fetch_background(topic):
    print("🎬 Fetching background footage...")
    query = topic.split("vs")[0].strip()
    headers = {"Authorization": PEXELS_KEY}
    params  = {"query": query, "per_page": 5, "orientation": "portrait"}
    r = requests.get("https://api.pexels.com/videos/search",
                     headers=headers, params=params)

    for video in r.json().get("videos", []):
        for f in video["video_files"]:
            if f.get("width") == 1080:
                data = requests.get(f["link"]).content
                with open("bg_video.mp4", "wb") as file:
                    file.write(data)
                print("✅ Background video downloaded")
                return True

    print("⚠️ No footage found, using dark background")
    return False

# ─────────────────────────────────────────────
# STEP 6 — Fetch thumbnail image from Pexels
# ─────────────────────────────────────────────
def fetch_thumbnail_image(topic):
    print("🖼️ Fetching thumbnail image...")
    query = topic.split("vs")[0].strip()
    headers = {"Authorization": PEXELS_KEY}
    params  = {"query": query, "per_page": 3, "orientation": "landscape"}
    r = requests.get("https://api.pexels.com/v1/search",
                     headers=headers, params=params)

    photos = r.json().get("photos", [])
    if photos:
        img_url = photos[0]["src"]["large"]
        img_data = requests.get(img_url).content
        img = Image.open(io.BytesIO(img_data)).convert("RGBA")
        print("✅ Thumbnail image fetched")
        return img

    print("⚠️ No image found, using solid background")
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
        # Darken it so text pops
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
        # Try system fonts first
        big_font   = ImageFont.truetype("LiberationSans-Bold.ttf", 96)
        small_font = ImageFont.truetype("LiberationSans-Bold.ttf", 38)
        tiny_font  = ImageFont.truetype("LiberationSans-Regular.ttf", 28)
    except:
        try:
            # Fallback to Arial
            big_font   = ImageFont.truetype("arial.ttf", 96)
            small_font = ImageFont.truetype("arial.ttf", 38)
            tiny_font  = ImageFont.truetype("arial.ttf", 28)
        except:
            # Ultimate fallback
            big_font = small_font = tiny_font = ImageFont.load_default()

    # Main big text (2 lines max)
    words   = thumbnail_text.upper().split()
    line1   = " ".join(words[:len(words)//2]) if len(words) > 2 else thumbnail_text.upper()
    line2   = " ".join(words[len(words)//2:]) if len(words) > 2 else ""

    # Shadow effect
    shadow_offset = 4
    draw.text((84, 254), line1, font=big_font, fill=(0, 0, 0, 180))
    draw.text((80, 250), line1, font=big_font, fill=(255, 220, 0))
    if line2:
        draw.text((84, 354), line2, font=big_font, fill=(0, 0, 0, 180))
        draw.text((80, 350), line2, font=big_font, fill=(255, 255, 255))

    # ── Subtitle (title) ──
    wrapped = textwrap.fill(title, width=35)
    lines   = wrapped.split("\n")[:2]
    y_start = 490 if line2 else 390
    for i, line in enumerate(lines):
        draw.text((82, y_start + 2 + i * 46), line, font=small_font, fill=(0, 0, 0, 160))
        draw.text((80, y_start + i * 46),      line, font=small_font, fill=(220, 220, 220))

    # ── Bottom bar ──
    draw.rectangle([(0, H - 60), (W, H)], fill=(255, 200, 0, 220))
    draw.text((40, H - 46), "WATCH NOW  →  Tech 8ytees", font=tiny_font, fill=(10, 10, 20))

    # ── Save ──
    thumb_rgb = thumb.convert("RGB")
    thumb_rgb.save("thumbnail.jpg", "JPEG", quality=95)
    print("✅ Thumbnail saved: thumbnail.jpg")

# ─────────────────────────────────────────────
# STEP 8 — Assemble the Short video (FFmpeg)
# ─────────────────────────────────────────────
def create_video(title, has_video):
    print("🎞️ Assembling video with FFmpeg...")
    import subprocess

    try:
        # Get audio duration
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "voiceover.mp3"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"⚠️ ffprobe error: {result.stderr}")
            return
            
        duration = float(result.stdout.strip())
        # Add 4 seconds for subscribe CTA at the end
        video_duration = duration + 4

        if has_video:
            # Use background video + audio + text overlay + animated subscribe CTA
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
            # Dark background + audio + text overlay + animated subscribe CTA
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
            print(f"⚠️ FFmpeg error: {result.stderr}")
            return
            
        print("✅ Video ready: output.mp4 (with subscribe CTA)")
        
    except subprocess.TimeoutExpired:
        print("❌ Video assembly timed out")
    except Exception as e:
        print(f"❌ Video assembly failed: {e}")

# ─────────────────────────────────────────────
# STEP 9 — Upload to YouTube with thumbnail
# ─────────────────────────────────────────────
def upload_to_youtube(title, description, tags):
    print("📤 Uploading to YouTube...")
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

    # Upload video
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
        print("   (Enable thumbnail uploads in YouTube Studio settings)")

    return video_id

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n🚀 Tech 8ytees Automation — {date.today()}\n{'─'*45}")

    topic     = get_todays_topic()
    raw       = generate_script(topic)
    parsed    = parse_script(raw)

    generate_voiceover(parsed["script"])
    has_video = fetch_background(topic)
    create_thumbnail(parsed["title"], parsed["thumbnail_text"], topic)
    create_video(parsed["title"], has_video)
    upload_to_youtube(parsed["title"], parsed["description"], parsed["tags"])

    print(f"\n{'─'*45}\n🎉 Done! Video + Thumbnail posted to Tech 8ytees!\n")