import os
try:
    from instagrapi import Client
except ImportError:
    print("⚠️ instagrapi not installed. Please pip install instagrapi")
    Client = None

def upload_to_instagram(video_path, caption):
    """
    Uploads the generated video to Instagram Reels.
    Requires IG_USERNAME and IG_PASSWORD environment variables.
    """
    print("📤 Uploading to Instagram Reels...")
    
    username = os.environ.get("IG_USERNAME")
    password = os.environ.get("IG_PASSWORD")
    
    if not username or not password:
        print("❌ IG_USERNAME or IG_PASSWORD not set. Cannot upload to Instagram.")
        return False
        
    if not Client:
        return False
        
    if not os.path.exists(video_path):
        print(f"❌ Video file {video_path} not found.")
        return False

    try:
        cl = Client()
        # Optional: You can load session to avoid repetitive logins, e.g. cl.load_settings("session.json")
        print(f"   Logging in as {username}...")
        cl.login(username, password)
        # cl.dump_settings("session.json")
        
        print("   Uploading Reel...")
        media = cl.clip_upload(
            video_path,
            caption
        )
        print(f"✅ Successfully uploaded Instagram Reel! URL: https://instagram.com/reel/{media.code}")
        return True
        
    except Exception as e:
        print(f"❌ Instagram upload failed: {e}")
        return False
