import os
import time
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
    
    Note: If you encounter "IP blacklisted" errors, Instagram has temporarily
    blocked your IP. Solutions:
    - Use a proxy/VPN in production
    - Use GitHub Actions with different runners
    - Consider using official Instagram Graph API instead
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

    max_retries = 3
    for attempt in range(max_retries):
        try:
            cl = Client()
            print(f"   Attempt {attempt + 1}/{max_retries}: Logging in as {username}...")
            cl.login(username, password)
            
            print("   Uploading Reel...")
            
            # Ensure we have Instagram Reels tags
            if "#reels" not in caption.lower():
                caption = f"{caption}\n\n#Reels #InstagramReels #TechReels"
                
            media = cl.clip_upload(
                video_path,
                caption
            )
            print(f"✅ Instagram Reel uploaded! URL: https://instagram.com/reel/{media.code}")
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            if "blacklist" in error_msg or "ip" in error_msg:
                print(f"⚠️ Attempt {attempt + 1}: IP blacklisted by Instagram")
                print("   This is a security measure. Instagram blocks repeated login attempts.")
                print("   Solutions:")
                print("   1. Wait 24-48 hours before retrying")
                print("   2. Use official Instagram Graph API with business account")
                print("   3. Use a proxy/VPN to change IP (in production)")
                if attempt < max_retries - 1:
                    wait_time = 30 * (attempt + 1)
                    print(f"   Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                continue
            elif "incorrect" in error_msg or "password" in error_msg:
                print(f"❌ Login failed: Invalid username or password")
                return False
            else:
                print(f"❌ Instagram upload failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    print(f"   Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
    print("❌ Instagram upload failed after all retry attempts")
    return False
