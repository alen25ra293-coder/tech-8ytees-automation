import os
import requests
import time

def upload_to_instagram_graphapi(video_path, caption):
    """
    Uploads to Instagram using the Official Graph API.
    Most reliable method - no IP blacklist issues.
    
    Required Environment Variables:
    - IG_BUSINESS_ACCOUNT_ID: Your Instagram Business Account ID
    - IG_GRAPH_ACCESS_TOKEN: Long-lived Graph API access token
    
    Setup:
    1. Go to https://developers.facebook.com/
    2. Create a Facebook App (Business category)
    3. Add "Instagram Graph API" product
    4. Get your Business Account ID from Instagram Settings
    5. Generate a long-lived access token (expires in ~60 days)
    6. Store both in GitHub Secrets
    """
    print("📤 Uploading to Instagram via Graph API...")
    
    # Load environment variables
    business_account_id = os.environ.get("IG_BUSINESS_ACCOUNT_ID")
    access_token = os.environ.get("IG_GRAPH_ACCESS_TOKEN")
    
    if not business_account_id or not access_token:
        print("⚠️ Graph API credentials missing:")
        if not business_account_id:
            print("   - IG_BUSINESS_ACCOUNT_ID not set")
        if not access_token:
            print("   - IG_GRAPH_ACCESS_TOKEN not set")
        return False
    
    if not os.path.exists(video_path):
        print(f"❌ Video file {video_path} not found.")
        return False
    
    try:
        # Step 1: Initialize upload (for large files, use resumable upload)
        print("   Initializing upload...")
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
            print(f"   Media created: {media_id}")
            
            # Step 2: Publish the media
            print("   Publishing Reel...")
            publish_url = f"https://graph.instagram.com/v19.0/{business_account_id}/media_publish"
            publish_data = {
                'creation_id': media_id,
                'access_token': access_token
            }
            
            publish_response = requests.post(publish_url, json=publish_data, timeout=60)
            
            if publish_response.status_code == 200:
                post_id = publish_response.json().get('id')
                print(f"✅ Instagram Reel published! ID: {post_id}")
                print(f"   URL: https://instagram.com/reel/{post_id}")
                return True
            else:
                print(f"❌ Failed to publish: {publish_response.text}")
                return False
        else:
            error_msg = response.json().get('error', {}).get('message', response.text)
            if "token" in error_msg.lower() or "invalid" in error_msg.lower():
                print(f"❌ Invalid Graph API token or credentials")
                print(f"   Error: {error_msg}")
            else:
                print(f"❌ Upload failed: {error_msg}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Upload timed out (video too large?)")
        return False
    except Exception as e:
        print(f"❌ Graph API error: {e}")
        return False


def get_graphapi_setup_instructions():
    """Return setup instructions for Graph API"""
    return """
🔑 Instagram Graph API Setup Instructions
────────────────────────────────────────

1. Go to https://developers.facebook.com/
2. Click "My Apps" → Create App
   - App Type: Business
   - App Name: Tech 8ytees Automation
   
3. Add "Instagram Graph API" product to your app

4. In App Settings → Basic, get:
   - App ID
   - App Secret

5. In Meta Business Suite (https://business.facebook.com):
   - Connect your Instagram Business Account
   - Get your Instagram Business Account ID

6. Generate an Access Token:
   - Go to Tools → Access Token Debugger
   - Create a long-lived token (valid ~60 days)
   - Permissions needed: instagram_business_content_publish

7. Add to GitHub Secrets:
   - IG_BUSINESS_ACCOUNT_ID=your_business_account_id
   - IG_GRAPH_ACCESS_TOKEN=your_access_token

📚 Full docs: https://developers.facebook.com/docs/instagram-api
"""
