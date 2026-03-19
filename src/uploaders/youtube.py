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


def upload_to_youtube(title: str, description: str, tags: str, video_file: str = "output.mp4"):
    """
    Upload a video to YouTube Shorts.
    Reads credentials from token.json (written by GitHub Actions from the YOUTUBE_TOKEN_JSON secret).
    Returns the video ID on success, None on failure.
    """
    if not os.path.exists(video_file):
        print(f"❌ Video file not found: {video_file}")
        return None

    if not os.path.exists("token.json"):
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

        if "#shorts" not in description.lower():
            upload_description = f"{description}\n\n#Shorts #Tech8ytees #TechShorts #Gadgets"
        else:
            upload_description = description

        # Normalise tags: accept both string and list
        if isinstance(tags, str):
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        else:
            tag_list = tags

        # Add channel-specific tags
        base_tags = ["Tech8ytees", "TechShorts", "Gadgets", "Shorts", "Tech"]
        tag_list = list(dict.fromkeys(tag_list + base_tags))[:15]  # deduplicate, cap at 15

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
        return video_id

    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        return None
