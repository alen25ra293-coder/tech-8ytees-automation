import sys
from datetime import date
import os
from dotenv import load_dotenv
load_dotenv()
import json
import requests
import argparse
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

def extract_strategy_insights() -> dict:
    """Reads the weekly strategy JSON and asks the AI to strictly extract automation variables."""
    strategy_path = "reports/latest_strategy_context.json"
    if not os.path.exists(strategy_path):
        print("⚠️ No weekly strategy report found. Automation will use fallback behavior.")
        return {}

    print("🧠 Extracting dynamic insights and formulas from Weekly Strategy Report...")
    try:
        with open(strategy_path, "r", encoding="utf-8") as f:
            strat = json.load(f)

        prompt = f"""
        Act as an AI data extractor. Read the following YouTube Strategy components:
        
        [COMPETITOR ANALYSIS]
        {strat.get('competitor_analysis', '')}
        
        [SCRIPT FRAMEWORK & OUTLINES]
        {strat.get('script_framework', '')}
        {strat.get('script_outlines', '')}

        [THUMBNAIL STRATEGY]
        {strat.get('thumbnail_strategy', '')}

        Extract the following fields in strict JSON format mapping EXACTLY to these keys. DO NOT output any markdown blocks, just raw JSON:
        {{
            "hook_formula": "The single best performing short hook structure/sentence recommended",
            "competitor_hook_styles": "A 1-2 sentence summary of how competitors pace and style their videos",
            "content_series": "A 1-3 word series theme name recommended (e.g. 'Hidden Gem' or 'Cheap vs Expensive')",
            "thumbnail_style": "Specific visual instructions for thumbnail generation (e.g. Dark background, Neon green accent, large text)",
            "hashtags": "3 to 5 highly relevant comma-separated hashtags (e.g. #tech, #gadget)",
            "call_to_action": "The exact call to action line recommended for the end",
            "title_formula": "The exact title format recommended (e.g. 'THIS $20 [Product] DESTROYS [Competitor]')"
        }}
        """
        
        # Use _generate_with_retry from script module if needed, or define locally
        from src.generators.script import _generate_with_retry
        response_text = _generate_with_retry(prompt)
        
        # Clean markdown wrappers if any
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        insights = json.loads(response_text.strip())
        print("   ✅ Strategy insights successfully parsed!")
        return insights
    except Exception as e:
        print(f"   ⚠️ Failed to extract insights from strategy: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(description="Tech 8ytees Video Automation Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Generate script only, do not build video or upload")
    parser.add_argument("--no-upload", action="store_true", help="Build video but skip YouTube/Instagram upload")
    args = parser.parse_args()

    if sys.platform == "win32":
        import io
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        elif hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print(f"\n🚀 Tech 8ytees — Budget Gadgets & Hidden Gems — {date.today()}\n{'─' * 48}")

    try:
        # ── 0. Assets ────────────────────────────────────────────────────
        download_impact_sound()
        
        # ── 0.5 Extract Weekly Strategy ──────────────────────────────────
        insights = extract_strategy_insights()

        # ── 1. Topic (niched: budget gadgets & hidden gems under $50) ─────
        topic = None
        weekly_ideas_file = "weekly_ideas.txt"
        if os.path.exists(weekly_ideas_file):
            with open(weekly_ideas_file, "r", encoding="utf-8") as f:
                ideas = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if ideas:
                raw_idea = ideas.pop(0)
                # Clean up "Title: ... - Hook: ..." format
                topic = raw_idea
                if "Title:" in raw_idea:
                    topic = raw_idea.split("Title:")[1].split("- Hook:")[0].strip()
                
                print(f"📖 Using Weekly Strategy Idea: {topic}")
                print(f"   ({len(ideas)} ideas remaining in queue)")
                
                # Consumes the idea by re-writing without it
                if not args.dry_run:
                    with open(weekly_ideas_file, "w", encoding="utf-8") as f:
                        f.write("\n".join(ideas) + "\n" if ideas else "")
        
        if not topic:
            print("⚠️ Queue empty or missing. Falling back to Reddit scraper for topic.")
            topic = get_todays_topic()

        # ── 2. Script (55-65 words → 23-26 second video) ─────────────────
        raw_script = generate_script(topic, insights=insights)
        parsed = parse_script(raw_script)

        if not parsed or not parsed.get("script"):
            print("❌ Failed to generate script. Exiting.")
            sys.exit(1)

        wc = len(parsed["script"].split())
        print(f"\n📝 Script: {wc} words  (target: 55-65 for 23-26s)\n")

        if args.dry_run:
            print("✅ Dry run complete. Stopping before video generation.")
            sys.exit(0)

        # ── 3. Niche hashtags (first comment, NOT caption) ────────────────
        extracted_tags = insights.get("hashtags", [])
        if extracted_tags:
            hashtags = " ".join(extracted_tags) if isinstance(extracted_tags, list) else extracted_tags
            print(f"🏷️  Using strategy hashtags: {hashtags}")
        else:
            hashtags = generate_dynamic_hashtags(topic)

        # ── 4. Voiceover (+18% speed for energy) ─────────────────────────
        if not generate_voiceover(parsed["script"]):
            print("❌ Voiceover generation failed. Exiting.")
            sys.exit(1)

        # ── 5. Background clips (10 clips × 2.5s each = rapid cuts for 23-26s) ────
        product_name = parsed.get("product_name")
        bg_clips = fetch_background_clips(topic, product_name=product_name, num_clips=10)
        if not bg_clips:
            print("⚠️ No background clips found. Continuing with fallback background.")

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
            title=parsed["title"],
            style=insights.get("thumbnail_style")
        )

        if args.no_upload:
            print("✅ Video generated. Skipping upload due to --no-upload flag.")
            sys.exit(0)

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

        cta = insights.get("call_to_action", "👇 Comment below!")
        ig_caption = f"{caption_hook}\n\n{parsed.get('description', '')}\n.\n.\n.\n{cta}"

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
