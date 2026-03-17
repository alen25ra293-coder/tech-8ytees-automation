import sys
from datetime import date
from src.scrapers.reddit import get_todays_topic
from src.generators.script import generate_script, parse_script
from src.tts.edge_voice import generate_voiceover
from src.video.pexels import fetch_background_clips
from src.video.composer import create_video
from src.uploaders.instagram import upload_to_instagram
from src.uploaders.youtube import upload_to_youtube

def main():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print(f"\n🚀 Tech 8ytees Modular Automation — {date.today()}\n{'─'*45}")

    try:
        topic = get_todays_topic()
        
        raw_script = generate_script(topic)
        parsed = parse_script(raw_script)
        
        if not parsed or not parsed.get("script"):
            print("❌ Failed to generate script. Exiting.")
            sys.exit(1)
            
        print(f"\n📝 Final Script Length: {len(parsed['script'].split())} words\n")
        
        success = generate_voiceover(parsed["script"])
        if not success:
            sys.exit(1)
            
        # Fetch 4 diverse clips to keep the background engaging
        bg_clips = fetch_background_clips(topic, num_clips=4)
        
        video_ok = create_video(parsed["title"], bg_clips)
        
        if video_ok:
            # Tell GH actions that output.mp4 is ready for YouTube
            upload_to_youtube(parsed["title"], parsed["description"], parsed["tags"])
            
            # Automatically upload to Instagram Reels directly here
            ig_caption = f"{parsed['title']}\n\n{parsed['description']}\n\n{parsed['tags']}"
            upload_to_instagram("output.mp4", ig_caption)
            
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
