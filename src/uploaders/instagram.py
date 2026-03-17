import os
try:
    from instagrapi import Client
except ImportError:
    Client = None
    print("[WARNING] instagrapi not installed. Run: pip install instagrapi")

def upload_to_instagram(video_path, caption):
    """
    Uploads the generated video to Instagram Reels.
    Reads credentials from:
    1. Environment variables (IG_USERNAME, IG_PASSWORD)
    2. .env file if available
    """
    print("📤 Uploading to Instagram Reels...")
    
    # Try to load from .env file first
    if os.path.exists(".env"):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
    
    username = os.environ.get("IG_USERNAME") or os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("IG_PASSWORD") or os.environ.get("INSTAGRAM_PASSWORD")
    
    if not username or not password:
        print("❌ IG_USERNAME and IG_PASSWORD not set in environment or .env file.")
        print("   Set these in GitHub Secrets or .env file to enable Instagram uploads.")
        return False
        
    if not Client:
        print("[ERROR] instagrapi not installed. Run: pip install instagrapi")
        return False
        
    if not os.path.exists(video_path):
        print(f"❌ Video file {video_path} not found.")
        return False

    try:
        cl = Client()
        print(f"   Logging in as {username}...")
        cl.login(username, password)
        
        print("   Uploading Reel...")
        media = cl.clip_upload(
            video_path,
            caption
        )
        print(f"✅ Instagram Reel uploaded! URL: https://instagram.com/reel/{media.code}")
        return True
        
    except Exception as e:
        print(f"❌ Instagram upload failed: {e}")
        return False
