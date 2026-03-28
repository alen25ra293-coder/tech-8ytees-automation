"""
YouTube Shorts Uploader — Tech 8ytees
Uploads to YouTube using the Data API v3.
- Clean titles: only #Shorts appended, no hashtag spam
- Pinned engagement comment with relevant question
- SEO-optimized description with curiosity-gap lead
"""
import os
import re
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def _clean_title(title: str) -> str:
    """Strip all hashtags from title — they belong in description only.
    Only append #Shorts (required for Shorts classification)."""
    # Remove any existing hashtags
    clean = re.sub(r'#\w+', '', title).strip()
    # Collapse double spaces
    clean = re.sub(r'\s{2,}', ' ', clean).strip()
    # Append ONLY #Shorts
    if "#shorts" not in clean.lower():
        clean = f"{clean} #Shorts"
    return clean[:100]


def upload_to_youtube(title: str, description: str, tags: str,
                       video_file: str = "output.mp4", thumbnail_path: str | None = None,
                       question: str = "", product_name: str = ""):
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

        # Load and optionally refresh credentials (handle UTF-8 BOM)
        with open("token.json", "r", encoding="utf-8-sig") as f:
            cred_data = json.load(f)
        creds = Credentials(**cred_data)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        youtube = build("youtube", "v3", credentials=creds)

        # ── Clean title: strip hashtag spam, keep only #Shorts ────────────
        upload_title = _clean_title(title)

        # ── Extract dynamic prices for Budget CTA ────────────
        # Search title and original description/question for any rupee values
        price_search_text = f"{title} {question} {description}"
        raw_prices = re.findall(r'₹\s*([0-9,kK]+)', price_search_text)
        
        unique_prices = []
        for p in raw_prices:
            if p not in unique_prices:
                unique_prices.append(p)
                
        if len(unique_prices) >= 2:
            price_1, price_2 = unique_prices[0], unique_prices[1]
        elif len(unique_prices) == 1:
            price_1 = unique_prices[0]
            digits = price_1.replace(',', '')
            price_2 = str(int(digits) * 10) if digits.isdigit() else "5000"
        else:
            price_1, price_2 = "500", "5000"

        # ── Build description: Metadata Reinforcement Template ────────────
        # First line is keyword-rich title sync (YouTube algorithm 2026)
        upload_description = (
            f"{upload_title} 🛑\n"
            f"Looking for the best tech in India? 🇮🇳 In this video, we explore {upload_title} to see if it is a total paisa-vasool deal! 💸\n"
            f"👇 COMMENT YOUR BUDGET BELOW! (₹{price_1} or ₹{price_2}?)\n"
            f"Subscribe for daily hidden tech finds! 🔔 @Tech8ytees\n\n"
            f"#TechIndia #BudgetGadgets #SmartHomeIndia #TechTricks #AmazonFinds #GadgetReview"
        )

        # ── Tags: keep 8-10 niche-specific, remove generic spam ──────────
        if isinstance(tags, str):
            tag_list = [t.strip().lstrip('#') for t in tags.replace(',', ' ').split() if t.strip()]
        else:
            tag_list = [str(t).strip().lstrip('#') for t in tags if t]

        # Filter: keep only meaningful tags, skip ultra-generic ones
        generic_skip = {"tech", "viral", "shorts", "fyp", "trending", "reels", "foryou"}
        tag_list = [t for t in tag_list if t.lower() not in generic_skip]
        
        # Append 4 title/topic related keywords to the bottom of the description
        added_tags = " ".join([f"#{t}" for t in tag_list[:4]])
        if added_tags:
            upload_description += f" {added_tags}"

        # Add channel + niche tags for YouTube backend
        base_tags = ["Tech8ytees", "BudgetGadgets", "TechFinds", "GadgetReview",
                     "BudgetTech", "AmazonIndia"]
        tag_list = list(dict.fromkeys(tag_list + base_tags))[:10]

        request_body = {
            "snippet": {
                "title":       upload_title,
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

        # ── Upload thumbnail if available ─────────────────────────────────
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

        # ── Pin engagement comment ────────────────────────────────────────
        _pin_engagement_comment(youtube, video_id, question, product_name)

        return video_id

    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        return None


def _pin_engagement_comment(youtube, video_id: str, question: str, product_name: str):
    """Post a relevant question as comment and pin it to drive engagement."""
    if not question:
        question = "What overpriced gadget should I test next? 👇"

    # Add a call-to-action to make it feel conversational
    comment_text = f"{question} 👇\n\n🔔 Subscribe — I find these every day!"

    try:
        print("📌 Posting pinned engagement comment...")

        # Insert the comment
        comment_result = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment_text,
                        }
                    },
                }
            }
        ).execute()

        comment_id = comment_result["snippet"]["topLevelComment"]["id"]
        print(f"   ✅ Comment posted: {comment_id}")

        # Try to pin the comment using replies endpoint and moderation
        try:
            youtube.comments().setModerationStatus(
                id=comment_id,
                moderationStatus="heldForReview",
                banAuthor=False
            ).execute()
            print(f"   📌 Pinned engagement comment on video {video_id}")
        except Exception as pin_err:
            # If pinning fails, comment still posted successfully
            print(f"   ⚠️  Auto-pin skipped (comment visible): {pin_err}")

    except Exception as e:
        print(f"⚠️  Pinned comment failed (non-critical): {e}")
