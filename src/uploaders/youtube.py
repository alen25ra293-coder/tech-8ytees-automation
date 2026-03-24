"""
YouTube Shorts Uploader
Uploads the generated video to YouTube using the Data API v3.
"""
import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def upload_to_youtube(title: str, description: str, tags: str,
                       video_file: str = "output.mp4", thumbnail_path: str | None = None):
    """
    Upload a video to YouTube Shorts.
    Reads credentials from token.json (written by GitHub Actions from the YOUTUBE_TOKEN_JSON secret).
    Returns the video ID on success, None on failure.
    """
    if not os.path.exists(video_file):
        print(f"❌ Video file not found: {video_file}")
        return None

    if not os.path.exists("token.json"):
        token_json_env = os.environ.get("YOUTUBE_TOKEN_JSON", "").strip()
        if token_json_env:
            try:
                parsed_token = json.loads(token_json_env)
                with open("token.json", "w", encoding="utf-8") as token_file:
                    json.dump(parsed_token, token_file)
                try:
                    os.chmod("token.json", 0o600)
                except OSError:
                    pass
                print("✅ token.json created from YOUTUBE_TOKEN_JSON.")
            except (json.JSONDecodeError, OSError) as e:
                print(f"⚠️  Invalid YOUTUBE_TOKEN_JSON value ({e}) — skipping YouTube upload.")
                print(f"   (Video is ready at: {video_file})")
                return None
        else:
            print("⚠️  No token.json found — skipping YouTube upload.")
            print(f"   (Video is ready at: {video_file})")
            return None

    try:
        print("📤 Uploading to YouTube Shorts...")

        # Load and optionally refresh credentials
        creds = Credentials.from_authorized_user_file("token.json")
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        youtube = build("youtube", "v3", credentials=creds)

        # Ensure #Shorts is in title/description for Shorts classification
        if "#shorts" not in title.lower():
            upload_title = f"{title} #Shorts"
        else:
            upload_title = title

        # Build SEO-optimized description
        # First line is keyword-rich (YouTube uses it in search results)
        upload_description = (
            f"{description}\n\n"
            f"🔔 Subscribe for daily tech shorts!\n"
            f"📱 Follow us on Instagram: @Tech8ytees\n\n"
            f"#Shorts #Tech8ytees #TechShorts #Gadgets #TechReview #Tech #Viral"
        )

        # Normalise tags: accept both string and list
        if isinstance(tags, str):
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        else:
            tag_list = tags

        # Add channel-specific tags for maximum discoverability
        base_tags = [
            "Tech8ytees", "TechShorts", "Gadgets", "Shorts", "Tech",
            "TechReview", "Viral", "TechTok", "GadgetReview", "BudgetTech"
        ]
        tag_list = list(dict.fromkeys(tag_list + base_tags))[:20]  # deduplicate, cap at 20

        request_body = {
            "snippet": {
                "title":       upload_title[:100],   # YouTube max title length
                "description": upload_description[:5000],
                "tags":        tag_list,
                "categoryId":  "28",  # 28 = Science & Technology
            },
            "status": {
                "privacyStatus":           "public",
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(video_file, mimetype="video/mp4", resumable=True)
        insert_req = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = insert_req.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"   ↑ Upload progress: {pct}%")

        video_id = response["id"]
        print(f"✅ YouTube upload successful! Video ID: {video_id}")
        print(f"   URL: https://youtube.com/shorts/{video_id}")

        # Upload thumbnail if available
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                print("🖼️  Setting custom thumbnail...")
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
                ).execute()
                print("✅ Thumbnail set successfully.")
            except Exception as thumb_err:
                print(f"⚠️  Thumbnail upload failed (non-critical): {thumb_err}")

        return video_id

    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        return None
