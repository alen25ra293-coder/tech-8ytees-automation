import sys
from datetime import date
import os
import requests
from src.scrapers.reddit import get_todays_topic
from src.generators.script import generate_script, parse_script, generate_dynamic_hashtags
from src.tts.edge_voice import generate_voiceover
from src.video.pexels import fetch_background_clips
from src.video.composer import create_video
from src.video.thumbnail import generate_thumbnail
from src.uploaders.instagram import upload_to_instagram
from src.uploaders.youtube import upload_to_youtube


def download_impact_sound():
    """Automatically downloads a free cinematic impact sound for the audio hook."""
    target = "assets/impact_sound.mp3"
    if os.path.exists(target):
        return True

    print("🔊 Downloading cinematic impact sound effect...")
    os.makedirs("assets", exist_ok=True)
    url = "https://assets.mixkit.co/active_storage/sfx/1143/1143.mp3"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            with open(target, "wb") as f:
                f.write(resp.content)
            print(f"   ✅ Saved to {target}")
            return True
        else:
            print(f"   ⚠️ Download failed with status {resp.status_code}")
    except Exception as e:
        print(f"   ⚠️ Could not download impact sound: {e}")
    return False


def main():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print(f"\n🚀 Tech 8ytees — Budget Gadgets & Hidden Gems — {date.today()}\n{'─' * 48}")

    try:
        # ── 0. Assets ────────────────────────────────────────────────────
        download_impact_sound()

        # ── 1. Topic (niched: budget gadgets & hidden gems under $50) ─────
        topic = get_todays_topic()

        # ── 2. Script (60-75 words → 25-30 second video) ─────────────────
        raw_script = generate_script(topic)
        parsed = parse_script(raw_script)

        if not parsed or not parsed.get("script"):
            print("❌ Failed to generate script. Exiting.")
            sys.exit(1)

        wc = len(parsed["script"].split())
        print(f"\n📝 Script: {wc} words  (target: 60-75 for 25-30s)\n")

        # ── 3. Niche hashtags (first comment, NOT caption) ────────────────
        hashtags = generate_dynamic_hashtags(topic)

        # ── 4. Voiceover (+18% speed for energy) ─────────────────────────
        if not generate_voiceover(parsed["script"]):
            print("❌ Voiceover generation failed. Exiting.")
            sys.exit(1)

        # ── 5. Background clips (12 clips × 3s each = rapid cuts) ────────
        bg_clips = fetch_background_clips(topic, num_clips=12)

        # ── 6. Video composition (title overlay + rapid cuts + subtitles) ─
        video_ok = create_video(
            title=parsed["title"],
            video_clips=bg_clips,
            hook_line=parsed.get("hook_line", ""),
        )
        if not video_ok:
            print("❌ Video assembly failed. Exiting.")
            sys.exit(1)

        # ── 7. Thumbnail ──────────────────────────────────────────────────
        thumbnail_path = generate_thumbnail(
            thumbnail_text=parsed.get("thumbnail_text", topic[:20]),
            title=parsed["title"]
        )

        # ── 8. YouTube upload ─────────────────────────────────────────────
        upload_to_youtube(
            title=parsed["title"],
            description=parsed["description"],
            tags=parsed["tags"],
            video_file="output.mp4",
            thumbnail_path=thumbnail_path,
        )

        # ── 9. Instagram upload ───────────────────────────────────────────
        # Caption: curiosity-gap hook only (NO hashtags in caption body)
        # Hashtags: posted as first comment (Instagram confirmed better reach)
        # Question: pinned as comment for engagement trigger
        caption_hook = parsed.get("caption_hook", "")
        if not caption_hook:
            caption_hook = "This gadget costs less than lunch but beats $300 products 👀"

        ig_caption = f"{caption_hook}\n\n{parsed['description']}"

        upload_to_instagram(
            video_path="output.mp4",
            caption=ig_caption,
            hashtags=hashtags,
            question=parsed.get("question", "What overpriced gadget should I expose next?"),
        )

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

