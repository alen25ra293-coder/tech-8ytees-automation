import sys
from datetime import date
import os
import requests
from src.generators.idea_bank import get_best_idea, mark_topic_used
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

    print(f"\n🚀 Tech 8ytees — Budget Gadgets & Hidden Gems — {date.today()}\n{'─' * 52}")

    topic = None  # track for deduplication after upload

    try:
        # ── 0. Assets ────────────────────────────────────────────────────
        download_impact_sound()

        # ── 1. Topic via Idea Bank (AI-powered, deduplicated) ─────────────
        # Idea Bank generates 5 ideas, self-rates for virality (1-10),
        # skips already-used topics, and returns the best fresh idea.
        topic = get_best_idea()

        # ── 2. Script (50-70 words → 23-26 second video) ──────────────────
        raw_script = generate_script(topic)
        parsed = parse_script(raw_script)

        if not parsed or not parsed.get("script"):
            print("❌ Failed to generate script. Exiting.")
            sys.exit(1)

        wc = len(parsed["script"].split())
        hook_style = parsed.get("hook_style", "unknown")
        print(f"\n📝 Script: {wc} words  (target: 50-70 for 23-26s) | Hook style: {hook_style}")

        # Show visual instructions for reference/debugging
        if parsed.get("visual_instructions"):
            print(f"🎥 Visuals: {parsed['visual_instructions'][:120]}...")

        print()

        # ── 3. Niche hashtags (first comment, NOT caption) ─────────────────
        hashtags = generate_dynamic_hashtags(topic)

        # ── 4. Voiceover (+18% speed for energy) ──────────────────────────
        if not generate_voiceover(parsed["script"]):
            print("❌ Voiceover generation failed. Exiting.")
            sys.exit(1)

        # ── 5. Background clips (10 clips × 2.5s = rapid cuts for 23-26s) ─
        product_name = parsed.get("product_name")
        print(f"🎬 Hook Style: {parsed['hook_style']} | Title: {parsed['title']}")
        print(f"🎥 Visual Instructions:\n{parsed['visual_instructions']}\n")
        bg_clips = fetch_background_clips(topic, product_name=product_name, num_clips=10)

        # ── 6. Video composition (title overlay + rapid cuts + subtitles) ──
        video_ok = create_video(
            title=parsed["title"],
            video_clips=bg_clips,
            hook_line=parsed.get("hook_line", ""),
        )
        if not video_ok:
            print("❌ Video assembly failed. Exiting.")
            sys.exit(1)

        # ── 7. Thumbnail ───────────────────────────────────────────────────
        thumbnail_path = generate_thumbnail(
            thumbnail_text=parsed.get("thumbnail_text", topic[:20]),
            title=parsed["title"]
        )

        # ── 8. YouTube upload ──────────────────────────────────────────────
        upload_to_youtube(
            title=parsed["title"],
            description=parsed["description"],
            tags=parsed["tags"],
            video_file="output.mp4",
            thumbnail_path=thumbnail_path,
        )

        # ── 9. Instagram upload ────────────────────────────────────────────
        # Caption: curiosity-gap hook only (NO hashtags in caption body)
        # Hashtags: posted as first comment (Instagram confirmed better reach)
        caption_hook = parsed.get("caption_hook", "")
        if not caption_hook:
            caption_hook = "This gadget costs less than lunch but beats ₹15,000 products 👀"

        ig_caption = f"{caption_hook}\n\n{parsed['description']}"

        upload_to_instagram(
            video_path="output.mp4",
            caption=ig_caption,
            hashtags=hashtags,
            question=parsed.get("question", "What overpriced gadget should I expose next?"),
        )

        # ── 10. Mark topic as used (deduplication) ─────────────────────────
        if topic:
            mark_topic_used(topic)
            print(f"✅ Topic archived to used_topics.json")

        print(f"\n🎉 Done! Video published for: {topic[:60]}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
