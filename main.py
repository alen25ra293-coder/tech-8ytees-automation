import sys
from datetime import date
from src.scrapers.reddit import get_todays_topic
from src.generators.script import generate_script, parse_script, generate_dynamic_hashtags
from src.tts.edge_voice import generate_voiceover
from src.video.pexels import fetch_background_clips
from src.video.composer import create_video
from src.video.thumbnail import generate_thumbnail
from src.uploaders.instagram import upload_to_instagram
from src.uploaders.youtube import upload_to_youtube


def main():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print(f"\n🚀 Tech 8ytees Automation — {date.today()}\n{'─' * 48}")

    try:
        # ── 1. Topic ─────────────────────────────────────────────────────
        topic = get_todays_topic()

        # ── 2. Script ────────────────────────────────────────────────────
        raw_script = generate_script(topic)
        parsed = parse_script(raw_script)

        if not parsed or not parsed.get("script"):
            print("❌ Failed to generate script. Exiting.")
            sys.exit(1)

        print(f"\n📝 Script: {len(parsed['script'].split())} words\n")

        # ── 3. Dynamic hashtags ───────────────────────────────────────────
        hashtags = generate_dynamic_hashtags(topic)

        # ── 4. Voiceover ─────────────────────────────────────────────────
        if not generate_voiceover(parsed["script"]):
            print("❌ Voiceover generation failed. Exiting.")
            sys.exit(1)

        # ── 5. Background clips ───────────────────────────────────────────
        bg_clips = fetch_background_clips(topic, num_clips=4)

        # ── 6. Video composition ──────────────────────────────────────────
        video_ok = create_video(parsed["title"], bg_clips)
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
        # Caption structure:
        #   Line 1: curiosity-gap hook (shown before "more" button)
        #   Line 2: blank
        #   Line 3: description
        #   Line 4: dynamic hashtags
        caption_hook = parsed.get("caption_hook", "")
        if not caption_hook:
            caption_hook = f"The truth about this that nobody's talking about 👇"

        ig_caption = (
            f"{caption_hook}\n\n"
            f"{parsed['description']}\n\n"
            f"{hashtags} #Tech8ytees #Shorts #Reels"
        )
        upload_to_instagram("output.mp4", ig_caption)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
