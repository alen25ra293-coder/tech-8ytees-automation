import os, requests
from datetime import date
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from gtts import gTTS
from moviepy.editor import *
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
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
    "AI detector tools do they actually work 2026",
    "top AI search engines replacing Google 2026",
    "best AI video editing tools 2026",
    "how to use AI to build a website for free 2026",
    "AI tools for graphic designers 2026",
    "best local AI models you can run on your PC 2026",
    "best AI chatbots comparison 2026",
    "AI tools for freelancers to earn more 2026",
    "best AI translation tools 2026",
    "how to use AI for SEO 2026",
    "best AI tools for video thumbnails 2026",
    "AI tools for teachers and educators 2026",
    "best AI resume builders 2026",
    "how to automate your business with AI 2026",
    "best AI interior design tools 2026",
    "AI tools for podcast creation 2026",
    "best AI logo makers 2026",
    "how to use Copilot AI in Windows 2026",
    "best AI email writers 2026",
    "AI tools for data analysis 2026",
    "best AI meeting summarizers 2026",
    "AI tools for Instagram content creation 2026",
    "best AI code review tools 2026",
    "how to use AI to learn any skill faster 2026",
    "best AI customer support tools 2026",
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
    "how to set up a home server 2026",
    "best free photo editing software 2026",
    "how to recover deleted files for free 2026",
    "best screen recording software 2026",
    "how to use Google Drive like a pro 2026",

    # ── SMARTPHONE TIPS ───────────────────────────────
    "hidden Android features you never knew existed 2026",
    "iPhone tips and tricks 2026",
    "how to extend your phone battery life 2026",
    "best Android apps you should install 2026",
    "best iPhone apps you are missing out on 2026",
    "how to transfer data to new phone 2026",
    "best phone cases that actually protect 2026",
    "how to fix a slow Android phone 2026",
    "best Google Pixel tips and tricks 2026",
    "Samsung Galaxy hidden features 2026",

    # ── GAMING TECH ───────────────────────────────────
    "PS5 vs Xbox Series X which is better 2026",
    "best gaming laptop under $1000 2026",
    "PC gaming vs console gaming 2026",
    "best budget gaming PC build 2026",
    "Nintendo Switch best accessories 2026",
    "best cloud gaming services 2026",
    "how to improve FPS in any PC game 2026",
    "best gaming router for low latency 2026",
    "Steam Deck worth buying 2026",
    "best free PC games you should play 2026",
]

# ─────────────────────────────────────────────
# STEP 1 — Pick today's topic (rotates daily)
# ─────────────────────────────────────────────
def get_todays_topic():
    index = date.today().toordinal() % len(GADGET_TOPICS)
    topic = GADGET_TOPICS[index]
    print(f"📌 Today's topic: {topic}")
    return topic

# ─────────────────────────────────────────────
# STEP 2 — Generate script with Gemini AI
# ─────────────────────────────────────────────
def generate_script(topic):
    print("🤖 Generating script with Gemini...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    response = model.generate_content(f"""
You are a viral YouTube Shorts scriptwriter for a tech channel called "Tech 8ytees".

Write a punchy 60-second script about: "{topic}"

Format EXACTLY like this (no extra text):
TITLE: [Catchy title under 60 chars]
SCRIPT: [Full 60-second spoken script only, no stage directions]
TAGS: [10 tags separated by commas]
DESCRIPTION: [2 sentences with call to action]

Rules:
- Hook in first 3 seconds (shocking or surprising opener)
- Simple words, fast pace, energetic tone
- End with "Link in bio to grab it!"
- Sound like a real human reviewer
""")
    return response.text

# ─────────────────────────────────────────────
# STEP 3 — Parse Claude's response
# ─────────────────────────────────────────────
def parse_script(raw):
    data = {"title": "", "script": "", "tags": "", "description": ""}
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

    print(f"✅ Script parsed — Title: {data['title']}")
    return data

# ─────────────────────────────────────────────
# STEP 4 — Generate voiceover (ElevenLabs + gTTS fallback)
# ─────────────────────────────────────────────
def generate_voiceover(script_text):
    # Try ElevenLabs first (better quality)
    try:
        print("🎙️ Trying ElevenLabs...")
        client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
        audio_gen = client.generate(
            text=script_text,
            voice="Josh",
            model="eleven_monolingual_v1"
        )
        with open("voiceover.mp3", "wb") as f:
            for chunk in audio_gen:
                f.write(chunk)
        print("✅ ElevenLabs voiceover done")

    # If ElevenLabs fails or runs out, use gTTS for free
    except Exception as e:
        print(f"⚠️ ElevenLabs failed ({e}), using free gTTS...")
        tts = gTTS(text=script_text, lang='en', slow=False)
        tts.save("voiceover.mp3")
        print("✅ gTTS voiceover done")

# ─────────────────────────────────────────────
# STEP 5 — Fetch background footage (Pexels)
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

    print("⚠️  No footage found, using dark background")
    return False

# ─────────────────────────────────────────────
# STEP 6 — Assemble the Short video
# ─────────────────────────────────────────────
def create_video(title, has_video):
    print("🎞️  Assembling video...")
    audio    = AudioFileClip("voiceover.mp3")
    duration = audio.duration

    if has_video:
        bg = VideoFileClip("bg_video.mp4").subclip(0, duration).resize((1080, 1920))
    else:
        bg = ColorClip(size=(1080, 1920), color=(10, 10, 25), duration=duration)

    # Dark overlay so text is readable
    overlay = (ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=duration)
               .set_opacity(0.5))

    # Channel watermark
    watermark = (TextClip("Tech 8ytees ⚡", fontsize=34, color="white", font="Arial-Bold")
                 .set_position(("center", 80))
                 .set_duration(duration)
                 .set_opacity(0.85))

    # Title at bottom
    short_title = title[:55] + "..." if len(title) > 55 else title
    title_clip = (TextClip(short_title, fontsize=46, color="white",
                           font="Arial-Bold", size=(980, None), method="caption")
                  .set_position(("center", 1600))
                  .set_duration(duration))

    final = CompositeVideoClip([bg, overlay, watermark, title_clip])
    final = final.set_audio(audio)
    final.write_videofile("output.mp4", fps=30, codec="libx264",
                          audio_codec="aac", remove_temp=True)
    print("✅ Video ready: output.mp4")

# ─────────────────────────────────────────────
# STEP 7 — Upload to YouTube
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

    print(f"✅ Live at: https://youtube.com/shorts/{response['id']}")

# ─────────────────────────────────────────────
# MAIN — Runs everything in order
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n🚀 Tech 8ytees Automation — {date.today()}\n{'─'*45}")

    topic     = get_todays_topic()
    raw       = generate_script(topic)
    parsed    = parse_script(raw)
    
    generate_voiceover(parsed["script"])
    has_video = fetch_background(topic)
    create_video(parsed["title"], has_video)
    upload_to_youtube(parsed["title"], parsed["description"], parsed["tags"])

    print(f"\n{'─'*45}\n🎉 Done! Video posted to Tech 8ytees!\n")
