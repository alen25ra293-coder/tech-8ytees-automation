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
    target = "assets/impact_sound.mp3"
    if os.path.exists(target):
        return True
    print("🔊 Downloading impact sound...")
    os.makedirs("assets", exist_ok=True)
    url = "https://assets.mixkit.co/active_storage/sfx/1143/1143.mp3"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            with open(target, "wb") as f:
                f.write(resp.content)
            print(f"   ✅ Saved to {target}")
            return True
        print(f"   ⚠️  Download failed: {resp.status_code}")
    except Exception as e:
        print(f"   ⚠️  Could not download: {e}")
    return False


def main():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print(f"\n🚀 Tech 8ytees — {date.today()}\n{'─' * 52}")

    topic = None
    category = None

    try:
        # ── 0. Assets ────────────────────────────────────────────────────────
        download_impact_sound()

        # ── 1. Topic (returns topic + category for diversity enforcement) ────
        # idea_bank now returns (topic, category) to prevent same-category
        # videos back to back. Category is saved to used_topics.json.
        topic, category = get_best_idea()

        # ── 2. Script ────────────────────────────────────────────────────────
        raw_script = generate_script(topic)
        parsed = parse_script(raw_script)

        if not parsed or not parsed.get("script"):
            print("❌ Failed to generate script. Exiting.")
            sys.exit(1)

        # Format numbers in title (15000 → 15,000)
        import re as _re
        def _fmt_nums(s: str) -> str:
            return _re.sub(r'\b(\d{1,3})(\d{3})\b', lambda m: m.group(1) + ',' + m.group(2), s)
        parsed["title"] = _fmt_nums(parsed.get("title", topic))

        wc = len(parsed["script"].split())
        print(f"\n📝 Script: {wc} words | Structure: {parsed.get('hook_style','?')}")
        print(f"📢 Hook: {parsed.get('hook_line','')}")

        if parsed.get("visual_instructions"):
            print(f"🎥 Visuals: {parsed['visual_instructions'][:120]}...")
        print()

        # ── 3. Hashtags ──────────────────────────────────────────────────────
        hashtags = generate_dynamic_hashtags(topic)

        # ── 4. Voiceover ─────────────────────────────────────────────────────
        if not generate_voiceover(parsed["script"]):
            print("❌ Voiceover failed. Exiting.")
            sys.exit(1)

        # ── 5. Background clips ───────────────────────────────────────────────
        product_name = parsed.get("product_name")
        print(f"🎬 Fetching clips for: {parsed['title']}")
        bg_clips = fetch_background_clips(topic, product_name=product_name, num_clips=10)

        # ── 6. Video composition ──────────────────────────────────────────────
        video_ok = create_video(
            title=parsed["title"],
            video_clips=bg_clips,
            hook_line=parsed.get("hook_line", ""),
        )
        if not video_ok:
            print("❌ Video assembly failed. Exiting.")
            sys.exit(1)

        # ── 7. Thumbnail ──────────────────────────────────────────────────────
        thumbnail_path = generate_thumbnail(
            thumbnail_text=parsed.get("thumbnail_text", topic[:20]),
            title=parsed["title"]
        )

        # ── 8. YouTube upload ─────────────────────────────────────────────────
        upload_to_youtube(
            title=parsed["title"],
            description=parsed["description"],
            tags=parsed["tags"],
            video_file="output.mp4",
            thumbnail_path=thumbnail_path,
        )

        # ── 9. Instagram upload ───────────────────────────────────────────────
        caption_hook = parsed.get("caption_hook") or "This gadget costs less than lunch but beats ₹15,000 products 👀"
        ig_caption = f"{caption_hook}\n\n{parsed['description']}"

        upload_to_instagram(
            video_path="output.mp4",
            caption=ig_caption,
            hashtags=hashtags,
            question=parsed.get("question", "What overpriced gadget should I test next?"),
        )

        # ── 10. Archive topic + category ─────────────────────────────────────
        # Category saved so next run avoids same product category
        if topic:
            mark_topic_used(topic, category=category)
            print(f"✅ Archived: {topic[:60]} | Category: {category}")

        print(f"\n🎉 Done! Published: {topic[:60]}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
