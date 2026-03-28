import os
import time
import requests

def _upload_to_tmpfiles(video_path):
    """Upload to tmpfiles.org - most reliable for GitHub Actions."""
    try:
        with open(video_path, "rb") as f:
            resp = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": f},
                timeout=120,
            )
        data = resp.json()
        if data.get("status") == "success":
            # Convert the page URL to a direct download URL
            # tmpfiles.org page URLs: https://tmpfiles.org/123/file.mp4
            # Direct URL: https://tmpfiles.org/dl/123/file.mp4
            page_url = data["data"]["url"]
            return page_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception as e:
        print(f"   ⚠️  tmpfiles.org upload failed: {e}")
    return None

def upload_to_instagram(video_path, caption, hashtags="", question=""):
    """
    Uploads to Instagram Reels using the Official Graph API:
    1. Uploads local video to tmpfiles.org (temporary public URL)
    2. Creates a media container on Instagram
    3. Polls status until 'FINISHED'
    4. Publishes the Reel
    5. Adds hashtags and engagement question as comments
    """
    print("📤 Uploading to Instagram Reels via Official Graph API...")

    access_token = os.environ.get("IG_GRAPH_ACCESS_TOKEN", "").strip().replace('"', '').replace("'", "").strip()
    business_id = os.environ.get("IG_BUSINESS_ACCOUNT_ID", "").strip()

    if not access_token or not business_id:
        print("❌ Instagram Graph API credentials missing.")
        return False

    if not os.path.exists(video_path):
        print(f"❌ Video file {video_path} not found.")
        return False

    try:
        # ── 1. Upload video to temporary hosting ─────────────────────────────
        # Instagram Graph API requires a public URL to fetch the video.
        # tmpfiles.org is most reliable from GitHub Actions.
        video_url = None
        
        # Try tmpfiles.org first (most reliable)
        print("   ☁️  Uploading video to temporary hosting (tmpfiles.org)...")
        video_url = _upload_to_tmpfiles(video_path)
        
        if video_url:
            print(f"   ✅ Temporary link obtained")
        
        # Fallback to file.io
        if not video_url:
            print("   ☁️  Trying fallback (file.io)...")
            try:
                with open(video_path, "rb") as f:
                    resp = requests.post(
                        "https://file.io",
                        files={"file": f},
                        data={"expires": "1d"},
                        timeout=60,
                    )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("link"):
                        video_url = data["link"]
                        print(f"   ✅ file.io upload successful")
            except Exception as e:
                print(f"   ⚠️  file.io failed: {e}")
        
        if not video_url:
            print("   ❌ Could not obtain a public URL for the video.")
            return False

        # ── 2. Create Media Container ────────────────────────────────────────
        print("   📦 Creating Instagram media container...")
        # Include hashtags directly in the caption (max 15 relevant ones)
        # Split hashtags and limit to first 15
        if hashtags:
            tag_list = [t.strip() for t in hashtags.split() if t.startswith('#')][:15]
            clean_hashtags = ' '.join(tag_list)
            final_caption = (
                f"{caption}\n\n"
                f"🔖 Save this for later\n"
                f"📤 Share with a friend who overpays for tech\n\n"
                f"{clean_hashtags}"
            )
        else:
            final_caption = (
                f"{caption}\n\n"
                f"🔖 Save this for later\n"
                f"📤 Share with a friend who overpays for tech"
            )
        
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
