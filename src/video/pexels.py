import os
import requests
import re

PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

# Product category to search term mappings for better clip relevance
PRODUCT_SEARCH_TERMS = {
    "earbuds": ["wireless earbuds close up", "earbuds in hand", "person wearing earbuds", "earphones tech"],
    "headphones": ["headphones close up", "person wearing headphones", "audio listening"],
    "speaker": ["bluetooth speaker", "portable speaker", "speaker close up"],
    "charger": ["phone charging", "wireless charger", "charging cable", "power bank"],
    "camera": ["action camera", "camera close up", "photography gadget", "filming setup"],
    "projector": ["mini projector", "projector screen", "home cinema"],
    "keyboard": ["mechanical keyboard", "keyboard typing", "gaming keyboard"],
    "mouse": ["computer mouse", "gaming mouse", "mouse click"],
    "monitor": ["computer monitor", "portable screen", "display screen"],
    "light": ["led light", "ring light", "desk lamp", "studio lighting"],
    "cable": ["usb cable", "charging cable", "cable management"],
    "hub": ["usb hub", "laptop accessories", "desk setup"],
    "tripod": ["phone tripod", "selfie stick", "camera stand"],
    "phone": ["smartphone holding", "phone in hand", "mobile phone"],
    "laptop": ["laptop close up", "laptop typing", "laptop workspace"],
    "watch": ["smartwatch", "watch close up", "wrist technology"],
    "fan": ["portable fan", "handheld fan", "cooling device"],
    "ssd": ["ssd drive", "data storage", "hard drive"],
    "webcam": ["webcam close up", "video call", "streaming setup"],
    "mount": ["phone mount", "car mount", "desk mount"],
    "plug": ["smart plug", "power outlet", "electrical device"],
    "remote": ["remote control", "tv remote", "smart home"],
}


def _get_product_category(topic: str, product_name: str) -> str:
    """Extract the product category from topic or product name."""
    combined = f"{topic} {product_name}".lower()
    for category in PRODUCT_SEARCH_TERMS.keys():
        if category in combined:
            return category
    return None


def _build_search_queries(topic: str, product_name: str) -> list:
    """Build relevant search queries based on the actual product being discussed."""
    queries = []
    
    # Get category-specific search terms
    category = _get_product_category(topic, product_name)
    if category and category in PRODUCT_SEARCH_TERMS:
        queries.extend(PRODUCT_SEARCH_TERMS[category][:2])
    
    # Use specific product name if available
    if product_name and len(product_name) > 2:
        # Extract key product words (remove brand specifics that won't match)
        clean_name = re.sub(r'[A-Z]{2,}\d+', '', product_name)  # Remove model numbers like T13, 521
        words = [w for w in clean_name.split() if len(w) > 2]
        if words:
            queries.insert(0, " ".join(words[:2]))
    
    # Add tech-focused fallbacks that match gadget content
    queries.extend([
        "tech gadget close up",
        "unboxing product",
        "hands holding gadget",
        "tech review setup",
    ])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q.lower() not in seen:
            seen.add(q.lower())
            unique_queries.append(q)
    
    return unique_queries[:6]  # Max 6 different search queries


def fetch_background_clips(topic, product_name=None, num_clips=10):
    """
    Fetches background video clips from Pexels that match the content topic.
    Uses product-specific search terms for better relevance.
    """
    print(f"🎬 Fetching {num_clips} background clips for '{product_name or topic}'...")
    if not PEXELS_KEY:
        print("⚠️ PEXELS_API_KEY is not set.")
        return []

    headers = {"Authorization": PEXELS_KEY}
    clips_downloaded = []
    
    # Build relevant search queries based on the product
    search_queries = _build_search_queries(topic, product_name or "")
    print(f"   🔍 Search queries: {search_queries[:3]}...")

    for sq in search_queries:
        if len(clips_downloaded) >= num_clips:
            break

        params = {"query": sq, "per_page": 10, "orientation": "portrait", "size": "medium"}

        try:
            r = requests.get("https://api.pexels.com/videos/search",
                             headers=headers, params=params, timeout=10)
            if r.status_code != 200:
                continue

            videos = r.json().get("videos", [])

            for video in videos:
                if len(clips_downloaded) >= num_clips:
                    break

                # Find best resolution file
                best_file = None
                for f in video["video_files"]:
                    if f.get("width") == 1080:
                        best_file = f
                        break

                if not best_file and video["video_files"]:
                    best_file = sorted(
                        video["video_files"],
                        key=lambda x: x.get("width", 0),
                        reverse=True
                    )[0]

                if best_file:
                    try:
                        video_url = best_file["link"]
                        print(f"   📥 Clip {len(clips_downloaded) + 1}/{num_clips} ({sq[:20]}...)")
                        data = requests.get(video_url, timeout=15).content
                        filename = f"bg_clip_{len(clips_downloaded)}.mp4"
                        with open(filename, "wb") as file:
                            file.write(data)
                        clips_downloaded.append(filename)
                    except Exception as e:
                        print(f"   ⚠️ Clip download error: {e}")

        except Exception as e:
            print(f"⚠️ Search '{sq}' failed: {e}")

    print(f"✅ Fetched {len(clips_downloaded)} clips for rapid-cut background.")
    return clips_downloaded
