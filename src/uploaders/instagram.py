"""
Instagram Reels Uploader
========================
Uses the Official Meta Graph API (most reliable, no IP blacklisting).
Falls back to Instagrapi if Graph API credentials aren't set.

HOW THE GRAPH API WORKS (2-STEP FLOW):
  Step 1: Create a media container → pass `video_url` (public URL of the file)
           The API downloads it from that URL, so we need a public host.
           We use tmpfiles.org (free, no signup, auto-expires).
  Step 2: Poll until container status = FINISHED, then call media_publish.

GITHUB SECRETS NEEDED (add in repo Settings → Secrets):
  IG_BUSINESS_ACCOUNT_ID   – Your Instagram Business/Creator account numeric ID
  IG_GRAPH_ACCESS_TOKEN    – Long-lived user access token (valid ~60 days)
  IG_USERNAME              – (Fallback only) Instagram username
  IG_PASSWORD              – (Fallback only) Instagram password
"""

import os
import time
import requests

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def upload_to_instagram(video_path, caption):
    """
    Upload a video as an Instagram Reel using the Official Meta Graph API.

    Strategy (tries in order):
      1. Official Graph API  – no IP issues, most stable
      2. Manual fallback     – prints instructions
    """
    print("\n📤 Uploading to Instagram Reels...\n")

    if _try_graph_api(video_path, caption):
        return True

    print()
    print("❌ Graph API upload failed.")
    print("🔄 Fallback: Manual Upload")
    print(f"   Video ready at: {video_path}")
    print("   You can manually upload to Instagram Reels via the app.")
    return False


# ---------------------------------------------------------------------------
# Method 1 – Official Meta Graph API
# ---------------------------------------------------------------------------

def _try_graph_api(video_path, caption):
    """
    Upload via the Instagram Graph API.

    The API requires the video to be at a *publicly accessible URL*.
    We upload the local file to file.io (free, ephemeral, no account needed),
    get a short-lived public URL, then hand that URL to the Graph API.
    """
    print("   [1/2] Trying Instagram Graph API (Official)...")

    account_id  = os.environ.get("IG_BUSINESS_ACCOUNT_ID", "").strip()
    account_id   = os.environ.get("IG_BUSINESS_ACCOUNT_ID", "").strip()
    access_token = os.environ.get("IG_GRAPH_ACCESS_TOKEN", "").strip().replace('"', '').replace("'", "").strip()

    # Extra cleaning: access tokens never contain dots or newlines
    access_token = access_token.split('\n')[0].split('\r')[0].split('.')[0].strip()

    if not account_id or not access_token:
        print("       ⏭️  Graph API credentials not configured.")
        print("          → Add IG_BUSINESS_ACCOUNT_ID + IG_GRAPH_ACCESS_TOKEN to GitHub Secrets.")
        return False

    if not os.path.exists(video_path):
        print(f"       ❌ Video file not found: {video_path}")
        return False

    # --- Step A: Upload to a free public host so Graph API can fetch the file ---
    print("       📡 Uploading video to temporary public host...")
    # Try file.io first (works with Instagram when available)
    # Fall back to tmpfiles.org if file.io fails
    public_url = None
    
    # Attempt file.io with timeout to avoid GitHub Actions hangs
    try:
        print("       Trying file.io...")
        with open(video_path, "rb") as f:
            resp = requests.post(
                "https://file.io",
                files={"file": f},
                data={"expires": "1d"},
                timeout=30,
            )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success") and data.get("link"):
                public_url = data["link"]
                print("       ✅ file.io upload successful.")
    except Exception as e:
        print(f"       ⚠️  file.io failed ({e}), trying tmpfiles.org...")
    
    # Fall back to tmpfiles.org
    if not public_url:
        public_url = _upload_to_tmpfiles(video_path)
    
    if not public_url:
        print("       ❌ Could not obtain a public URL for the video.")
        return False
    print(f"       ✅ Public URL obtained.")

    # --- Step B: Create a media container ---
    print("       🎬 Creating Instagram media container...")
    clean_caption = _sanitize_caption(caption)

    # CRITICAL: Business/Creator accounts must use the FACEBOOK host for Instagram Graph API
    base_url = "https://graph.facebook.com/v19.0"
    
    container_url = f"{base_url}/{account_id}/media"
    container_payload = {
        "media_type":  "REELS",
        "video_url":   public_url,
        "caption":     clean_caption,
        "share_to_feed": "true",
        "access_token": access_token,
    }

    try:
        resp = requests.post(container_url, data=container_payload, timeout=60)
        resp_json = resp.json()
    except Exception as e:
        print(f"       ❌ Container creation request failed: {e}")
        return False

    if resp.status_code != 200 or "id" not in resp_json:
        err = resp_json.get("error", {}).get("message", resp.text)
        print(f"       ❌ Container creation failed: {err}")
        _print_graph_api_hints(err)
        return False

    creation_id = resp_json["id"]
    print(f"       ✅ Container created (ID: {creation_id})")

    # --- Step C: Poll until the container is FINISHED processing ---
    print("       ⏳ Waiting for video to finish processing...")
    if not _wait_for_container(base_url, creation_id, access_token):
        print("       ❌ Video processing timed out or failed.")
        return False

    # --- Step D: Publish the container ---
    print("       🚀 Publishing Reel...")
    publish_url = f"{base_url}/{account_id}/media_publish"
    publish_payload = {
        "creation_id":  creation_id,
        "access_token": access_token,
    }

    try:
        pub_resp = requests.post(publish_url, data=publish_payload, timeout=60)
        pub_json = pub_resp.json()
    except Exception as e:
        print(f"       ❌ Publish request failed: {e}")
        return False

    if pub_resp.status_code == 200 and "id" in pub_json:
        post_id = pub_json["id"]
        print(f"       ✅ Instagram Reel published!")
        print(f"           URL: https://www.instagram.com/reel/{post_id}/")
        return True
    else:
        err = pub_json.get("error", {}).get("message", pub_resp.text)
        print(f"       ❌ Publish failed: {err}")
        return False


def _wait_for_container(base_url, creation_id, access_token, max_wait=300, interval=10):
    """Poll the container status until FINISHED or timeout."""
    status_url = f"{base_url}/{creation_id}"
    params = {
        "fields": "status,status_code",
        "access_token": access_token,
    }
    waited = 0
    while waited < max_wait:
        try:
            r = requests.get(status_url, params=params, timeout=30)
            data = r.json()
            status_code = data.get("status_code", "")

            if status_code == "FINISHED":
                return True
            elif status_code == "ERROR":
                print(f"       ❌ Processing error: {data.get('status', '')}")
                return False
            else:
                print(f"       ... Status: {status_code or 'IN PROGRESS'} ({waited}s elapsed)")
        except Exception as e:
            print(f"       ⚠️  Status check error: {e}")

        time.sleep(interval)
        waited += interval

    return False  # timed out


def _upload_to_tmpfiles(video_path):
    """Fallback: upload to tmpfiles.org."""
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
            page_url = data["data"]["url"]
            # tmpfiles.org page URLs look like: https://tmpfiles.org/123/file.mp4
            # Direct URL: https://tmpfiles.org/dl/123/file.mp4
            return page_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception as e:
        print(f"       ⚠️  tmpfiles.org upload failed: {e}")
    return None


def _sanitize_caption(caption):
    """Ensure caption has Reels hashtags and stays under 2200 chars."""
    if "#reels" not in caption.lower():
        caption = (
            f"{caption}\n\n"
            f"#Reels #InstagramReels #TechReels #Tech8ytees "
            f"#TechTok #Viral #ExplorePage #TechShorts"
        )
    return caption[:2200]


def _print_graph_api_hints(error_msg):
    """Print helpful hints based on the error message."""
    error_lower = error_msg.lower()
    if "token" in error_lower or "oauth" in error_lower or "session" in error_lower:
        print("       💡 Hint: Your access token may have expired (they last ~60 days).")
        print("          Regenerate at: https://developers.facebook.com/tools/explorer/")
    elif "permission" in error_lower or "scope" in error_lower:
        print("       💡 Hint: Your token is missing required permissions.")
        print("          Required: instagram_basic, instagram_content_publish, pages_read_engagement")
    elif "account" in error_lower or "business" in error_lower:
        print("       💡 Hint: IG_BUSINESS_ACCOUNT_ID must be a numeric Instagram Business/Creator ID.")
        print("          Find it: Instagram Settings → Account → Professional Dashboard")
