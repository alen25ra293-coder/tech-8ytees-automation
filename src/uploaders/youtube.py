import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

def upload_to_youtube(title, description, tags, video_file="output.mp4"):
    """
    Upload video to YouTube Shorts.
    Works both locally (if token.json exists) and in GitHub Actions.
    """
    if not os.path.exists(video_file):
        print("❌ Video file not found.")
        return None
    
    # Check if we have credentials
    if not os.path.exists("token.json"):
        print("⚠️  No token.json found. YouTube upload requires authentication.")
        print("📤 YouTube Upload - Ready for GitHub Actions")
        print(f"✅ Video {video_file} is ready for upload.")
        return "READY_FOR_UPLOAD"
    
    try:
        print("📤 Uploading to YouTube Shorts...")
        
        # Load credentials from token.json
        creds = Credentials.from_authorized_user_file("token.json")
        youtube = build("youtube", "v3", credentials=creds)
        
        # Ensure #Shorts is in the title and description
        if "#shorts" not in title.lower():
            title = f"{title} #Shorts"
            
        if "#shorts" not in description.lower():
            description = f"{description}\n\n#Shorts"
            
        # Create tags string
        tags_str = ", ".join(tags) if isinstance(tags, list) else tags
        
        # Prepare request body
        request_body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags.split(", ") if isinstance(tags, str) else tags,
                "categoryId": "24"  # 24 = Entertainment
            },
            "status": {
                "privacyStatus": "public"
            }
        }
        
        # Upload video
        media = MediaFileUpload(video_file, mimetype="video/mp4", resumable=True)
        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )
        
        response = insert_request.execute()
        video_id = response["id"]
        print(f"✅ YouTube upload successful! Video ID: {video_id}")
        print(f"   URL: https://youtube.com/shorts/{video_id}")
        return video_id
        
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        return None
