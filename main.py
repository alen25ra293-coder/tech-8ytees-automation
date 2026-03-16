import os, requests
from datetime import date
import anthropic
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from moviepy.editor import *
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
ANTHROPIC_KEY  = os.environ["ANTHROPIC_API_KEY"]
ELEVENLABS_KEY = os.environ["ELEVENLABS_API_KEY"]
PEXELS_KEY     = os.environ["PEXELS_API_KEY"]

GADGET_TOPICS = [
    "budget smartphone vs flagship 2026",
    "best wireless earbuds under $50",
    "smartwatch Apple vs Samsung 2026",
    "best budget laptop 2025",
    "USB-C hub you didn't know you needed",
    "robot vacuum comparison 2026",
    "best mechanical keyboard under $100",
    "portable charger power bank comparison",
    "smart home gadget worth buying 2026",
    "gaming mouse comparison 2026",
    "best webcam for streaming 2026",
    "noise cancelling headphones budget vs premium",
    "hidden iPhone features nobody talks about",
    "best standing desk gadgets 2026",
    "coolest tech gadgets under $30",
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
# STEP 2 — Generate script with Claude AI
# ─────────────────────────────────────────────
def generate_script(topic):
    print("🤖 Generating script with Claude...")
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": f"""
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
"""
        }]
    )
    return msg.content[0].text

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
# STEP 4 — Generate voiceover with ElevenLabs
# ─────────────────────────────────────────────
def generate_voiceover(script_text):
    print("🎙️ Generating voiceover...")
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
    print("✅ Voiceover saved")

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
