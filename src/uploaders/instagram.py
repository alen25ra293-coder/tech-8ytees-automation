import os
import time
import requests

def upload_to_instagram(video_path, caption, hashtags="", question=""):
    """
    Uploads to Instagram Reels using the Official Graph API:
    1. Uploads local video to file.io (temporary public URL)
    2. Creates a media container on Instagram
    3. Polls status until 'FINISHED'
    4. Publishes the Reel
    5. Adds hashtags and engagement question as comments
    """
    print("📤 Uploading to Instagram Reels via Official Graph API...")

    access_token = os.environ.get("IG_GRAPH_ACCESS_TOKEN")
    business_id = os.environ.get("IG_BUSINESS_ACCOUNT_ID")

    if not access_token or not business_id:
        print("❌ Instagram Graph API credentials missing.")
        return False

    if not os.path.exists(video_path):
        print(f"❌ Video file {video_path} not found.")
        return False

    try:
        # ── 1. Upload video to temporary hosting ─────────────────────────────
        # Instagram Graph API requires a public URL to fetch the video.
        # Try multiple services with fallback for reliability.
        video_url = None
        
        # Try 0x0.st first (more reliable, no rate limits)
        print("   ☁️  Uploading video to temporary hosting (0x0.st)...")
        try:
            with open(video_path, "rb") as f:
                resp = requests.post("https://0x0.st", files={"file": f}, timeout=120)
            if resp.status_code == 200 and resp.text.strip().startswith("http"):
                video_url = resp.text.strip()
                print(f"   ✅ Temporary link: {video_url}")
        except Exception as e:
            print(f"   ⚠️  0x0.st failed: {e}")
        
        # Fallback to file.io if 0x0.st failed
        if not video_url:
            print("   ☁️  Trying fallback (file.io)...")
            try:
                with open(video_path, "rb") as f:
                    resp = requests.post("https://file.io", files={"file": f}, timeout=120)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        video_url = data.get("link")
                    except Exception:
                        print(f"   ⚠️  file.io returned invalid JSON: {resp.text[:100]}")
            except Exception as e:
                print(f"   ⚠️  file.io failed: {e}")
        
        # Fallback to transfer.sh
        if not video_url:
            print("   ☁️  Trying fallback (transfer.sh)...")
            try:
                with open(video_path, "rb") as f:
                    resp = requests.put(
                        "https://transfer.sh/video.mp4",
                        data=f,
                        headers={"Max-Days": "1"},
                        timeout=120
                    )
                if resp.status_code == 200 and resp.text.strip().startswith("http"):
                    video_url = resp.text.strip()
                    print(f"   ✅ Temporary link: {video_url}")
            except Exception as e:
                print(f"   ⚠️  transfer.sh failed: {e}")
        
        if not video_url:
            print("   ❌ All temporary hosting services failed.")
            return False

        # ── 2. Create Media Container ────────────────────────────────────────
        print("   📦 Creating Instagram media container...")
        final_caption = f"{caption}\n\nSave this before it disappears 👆"
        
        media_url = f"https://graph.facebook.com/v22.0/{business_id}/media"
        params = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": final_caption,
            "access_token": access_token
        }
        
        resp = requests.post(media_url, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"   ❌ Container creation failed: {resp.text}")
            return False
        
        container_id = resp.json().get("id")
        print(f"   ✅ Container ID: {container_id}")

        # ── 3. Wait for Processing ───────────────────────────────────────────
        print("   ⏳ Waiting for Instagram to process video...")
        status_url = f"https://graph.facebook.com/v22.0/{container_id}"
        status_params = {"fields": "status_code", "access_token": access_token}
        
        max_retries = 30
        for i in range(max_retries):
            time.sleep(10)
            res = requests.get(status_url, params=status_params).json()
            status = res.get("status_code", "").upper()
            
            if status == "FINISHED":
                print("   ✅ Processing complete.")
                break
            elif status == "ERROR":
                print(f"   ❌ Instagram processing error: {res}")
                return False
            
            if i % 3 == 0:
                print(f"   ... ({status})")
        else:
            print("   ❌ Processing timed out.")
            return False

        # ── 4. Publish Media ─────────────────────────────────────────────────
        print("   📣 Publishing Reel...")
        publish_url = f"https://graph.facebook.com/v22.0/{business_id}/media_publish"
        publish_params = {
            "creation_id": container_id,
            "access_token": access_token
        }
        
        resp = requests.post(publish_url, params=publish_params, timeout=30)
        if resp.status_code != 200:
            print(f"   ❌ Publish failed: {resp.text}")
            return False
        
        media_id = resp.json().get("id")
        print(f"   ✅ Published! Media ID: {media_id}")

        # ── 5. Add Comments (Hashtags + Question) ────────────────────────────
        comment_url = f"https://graph.facebook.com/v22.0/{media_id}/comments"
        
        if hashtags:
            try:
                requests.post(comment_url, params={"message": hashtags, "access_token": access_token})
                print("   ✅ Hashtags added in comments.")
            except Exception:
                pass
        
        if question:
            try:
                requests.post(comment_url, params={"message": f"{question} 👇", "access_token": access_token})
                print("   ✅ Engagement question added in comments.")
            except Exception:
                pass

        return True

    except Exception as e:
        print(f"❌ Instagram Graph API error: {e}")
        return False
