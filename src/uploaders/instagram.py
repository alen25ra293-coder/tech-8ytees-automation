import os
import time
try:
    from instagrapi import Client
except ImportError:
    Client = None
    print("[WARNING] instagrapi not installed. Run: pip install instagrapi")

def upload_to_instagram(video_path, caption):
    """
    Upload to Instagram with 3 methods and automatic fallback:
    
    1. Graph API (Official - Most Reliable)
    2. Instagrapi with Retry Logic (Backup)
    3. Manual Upload Instruction (Last Resort)
    
    Tries methods in order until one succeeds.
    """
    print("📤 Uploading to Instagram Reels...\n")
    
    # Method 1: Try Graph API (Official, most reliable)
    result = _try_graph_api(video_path, caption)
    if result:
        return True
    
    print()
    
    # Method 2: Try Instagrapi with Retry Logic
    result = _try_instagrapi(video_path, caption)
    if result:
        return True
    
    print()
    
    # Method 3: Fallback instructions
    print("❌ All automated methods failed.")
    print("🔄 Fallback: Manual Upload")
    print("   Video ready at: output.mp4")
    print("   You can manually upload to Instagram Reels")
    return False


def _try_graph_api(video_path, caption):
    """
    Try uploading via Instagram Official Graph API
    Most reliable but requires setup
    """
    print("   [1/3] Trying Instagram Graph API (Official)...")
    
    business_account_id = os.environ.get("IG_BUSINESS_ACCOUNT_ID")
    access_token = os.environ.get("IG_GRAPH_ACCESS_TOKEN")
    
    if not business_account_id or not access_token:
        print("       ⏭️  Graph API credentials not configured")
        print("          (Set IG_BUSINESS_ACCOUNT_ID + IG_GRAPH_ACCESS_TOKEN)")
        return False
    
    try:
        import requests
        
        print("       Uploading via Graph API...")
        init_url = f"https://graph.instagram.com/v19.0/{business_account_id}/media"
        
        with open(video_path, 'rb') as video_file:
            files = {'file': video_file}
            data = {
                'caption': caption,
                'media_type': 'REELS',
                'access_token': access_token
            }
            response = requests.post(init_url, files=files, data=data, timeout=300)
        
        if response.status_code == 200:
            media_id = response.json().get('id')
            
            # Publish the media
            publish_url = f"https://graph.instagram.com/v19.0/{business_account_id}/media_publish"
            publish_data = {
                'creation_id': media_id,
                'access_token': access_token
            }
            publish_response = requests.post(publish_url, json=publish_data, timeout=60)
            
            if publish_response.status_code == 200:
                post_id = publish_response.json().get('id')
                print(f"       ✅ Graph API Success!")
                print(f"           URL: https://instagram.com/reel/{post_id}")
                return True
            else:
                error = publish_response.json().get('error', {}).get('message', '')
                print(f"       ❌ Publish failed: {error}")
                return False
        else:
            error = response.json().get('error', {}).get('message', response.text)
            if "token" in error.lower():
                print(f"       ❌ Invalid Graph API token")
            else:
                print(f"       ❌ Upload failed: {error[:80]}")
            return False
            
    except ImportError:
        print("       ❌ requests library not installed")
        return False
    except Exception as e:
        print(f"       ❌ Error: {str(e)[:80]}")
        return False


def _try_instagrapi(video_path, caption):
    """
    Try uploading via Instagrapi (Backup method)
    May fail due to IP blacklist but has retry logic
    """
    print("   [2/3] Trying Instagrapi with Retry (Backup)...")
    
    if os.path.exists(".env"):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
    
    username = os.environ.get("IG_USERNAME") or os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("IG_PASSWORD") or os.environ.get("INSTAGRAM_PASSWORD")
    
    if not username or not password:
        print("       ⏭️  Instagrapi credentials not configured")
        print("          (Set IG_USERNAME + IG_PASSWORD)")
        return False
    
    if not Client:
        print("       ❌ instagrapi not installed")
        return False
    
    if not os.path.exists(video_path):
        print(f"       ❌ Video file not found")
        return False
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            cl = Client()
            print(f"       Attempt {attempt + 1}/{max_retries}: Logging in...")
            cl.login(username, password)
            
            # Ensure proper tags
            if "#reels" not in caption.lower():
                caption = f"{caption}\n\n#Reels #InstagramReels #TechReels"
            
            media = cl.clip_upload(video_path, caption)
            print(f"       ✅ Instagrapi Success!")
            print(f"           URL: https://instagram.com/reel/{media.code}")
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "blacklist" in error_msg or "ip" in error_msg:
                print(f"       ⚠️  Attempt {attempt + 1}: IP Blacklisted")
                if attempt < max_retries - 1:
                    wait_time = 30 * (attempt + 1)
                    print(f"          Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"       ❌ IP blacklisted (max retries exceeded)")
                    print(f"          Solution: Wait 24-48 hours or use Graph API")
                continue
                
            elif "incorrect" in error_msg or "password" in error_msg or "unauthorized" in error_msg:
                print(f"       ❌ Invalid username or password")
                return False
            else:
                print(f"       ❌ Error: {str(e)[:60]}")
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    print(f"          Retrying in {wait_time}s...")
                    time.sleep(wait_time)
    
    return False

