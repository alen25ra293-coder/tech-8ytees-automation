import os
import requests
import re

PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

# Product category to search term mappings - ONLY use visual search terms that exist on Pexels
# Brand names like "QCY T13" or "Anker" won't return results - use generic visual descriptions
PRODUCT_SEARCH_TERMS = {
    "earbuds": ["earbuds", "wireless earbuds", "earphones", "in ear headphones", "airpods"],
    "headphones": ["headphones", "over ear headphones", "wearing headphones", "listening music headphones"],
    "speaker": ["bluetooth speaker", "portable speaker", "wireless speaker", "speaker music"],
    "charger": ["phone charging", "wireless charging", "charging smartphone", "usb charger"],
    "power bank": ["power bank", "portable charger", "charging phone battery"],
    "camera": ["action camera", "small camera", "gopro camera", "vlogging camera"],
    "projector": ["mini projector", "portable projector", "home projector", "projector screen"],
    "keyboard": ["keyboard typing", "mechanical keyboard", "computer keyboard", "rgb keyboard"],
    "mouse": ["computer mouse", "gaming mouse", "wireless mouse"],
    "monitor": ["computer monitor", "portable monitor", "screen display"],
    "light": ["ring light", "led light", "desk lamp", "studio light"],
    "lamp": ["desk lamp", "led lamp", "reading lamp"],
    "cable": ["usb cable", "charging cable", "phone cable"],
    "hub": ["usb hub", "laptop dock", "tech accessories"],
    "tripod": ["phone tripod", "selfie stick", "camera tripod"],
    "phone": ["smartphone", "using phone", "phone in hand", "mobile phone"],
    "laptop": ["laptop computer", "typing laptop", "laptop desk"],
    "watch": ["smartwatch", "smart watch", "digital watch", "fitness watch"],
    "fan": ["portable fan", "handheld fan", "mini fan", "usb fan"],
    "ssd": ["hard drive", "ssd storage", "computer storage"],
    "webcam": ["webcam", "video call", "streaming camera"],
    "mount": ["phone mount", "car phone holder", "phone holder"],
    "plug": ["smart plug", "electrical outlet", "smart home"],
    "remote": ["remote control", "smart remote", "tv remote"],
    "cleaner": ["screen cleaner", "cleaning electronics", "tech cleaning"],
    "trackpad": ["trackpad", "touchpad", "laptop touchpad"],
    "adapter": ["phone adapter", "usb adapter", "tech adapter"],
    "led": ["led strip", "led lights", "rgb lights", "ambient lighting"],
}

# Expanded keyword detection - more ways to identify the product category
CATEGORY_KEYWORDS = {
    "earbuds": ["earbuds", "earbud", "airpods", "buds", "in-ear", "tws"],
    "headphones": ["headphones", "headphone", "over-ear", "on-ear"],
    "speaker": ["speaker", "speakers", "soundbar", "boombox"],
    "charger": ["charger", "charging", "magsafe"],
    "power bank": ["power bank", "powerbank", "portable charger", "battery pack"],
    "camera": ["camera", "gopro", "action cam", "dashcam"],
    "projector": ["projector", "mini projector"],
    "keyboard": ["keyboard", "keeb", "mechanical"],
    "mouse": ["mouse", "mice"],
    "monitor": ["monitor", "screen", "display", "portable monitor"],
    "light": ["light", "ring light", "led light"],
    "lamp": ["lamp", "desk lamp"],
    "tripod": ["tripod", "selfie stick", "stand"],
    "phone": ["phone", "smartphone", "iphone", "android"],
    "laptop": ["laptop", "macbook", "notebook"],
    "watch": ["watch", "smartwatch", "fitness tracker"],
    "fan": ["fan", "portable fan", "cooling"],
    "webcam": ["webcam", "web cam", "streaming"],
    "mount": ["mount", "holder", "stand"],
    "plug": ["plug", "smart plug", "outlet"],
    "led": ["led strip", "led lights", "rgb", "strip lights"],
    "cleaner": ["cleaner", "cleaning kit"],
    "hub": ["hub", "usb hub", "dock", "docking"],
    "cable": ["cable", "cord", "wire"],
    "adapter": ["adapter", "dongle"],
    "remote": ["remote", "controller"],
    "ssd": ["ssd", "hard drive", "storage", "portable drive"],
    "trackpad": ["trackpad", "touchpad"],
}


def _get_product_category(topic: str, product_name: str) -> str:
    """Extract the product category from topic or product name using keyword matching."""
    combined = f"{topic} {product_name}".lower()
    
    # Check each category's keywords
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in combined:
                return category
    return None


def _build_search_queries(topic: str, product_name: str) -> list:
    """Build highly relevant search queries based on the product.
    
    STRICT RULE: The product shown MUST be relevant to the topic.
    We NEVER use generic fallbacks like "tech gadget" because it ruins the relevance.
    We prioritize "holding [product]" so the first frame (hook) shows Proof of Human.
    """
    queries = []
    
    # Priority 1: Exact product name with high-energy terms
    if product_name:
        queries.append(f"using {product_name.lower()}")
        queries.append(f"hand holding {product_name.lower()}")
        queries.append(f"{product_name.lower()} review")
        queries.append(f"{product_name.lower()} unboxing")
    
    # Priority 2: Category with 'Proof of Human' terms
    category = _get_product_category(topic, product_name)
    if category and category in PRODUCT_SEARCH_TERMS:
        terms = PRODUCT_SEARCH_TERMS[category]
        # Mix generic with 'hand' or 'person' to ensure it doesn't look like a 3D render
        for t in terms:
            queries.append(f"hand holding {t}")
            queries.append(f"person using {t}")
            queries.append(f"{t} close up")
            queries.append(f"{t} unboxing")
    
    # Priority 3: Visual descriptors from topic
    topic_clean = re.sub(r'₹[\d,]+|vs|\$', '', topic.lower())
    words = [w for w in topic_clean.split() if len(w) > 3]
    if words:
        queries.append(" ".join(words[:2]))

    # Deduplicate while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            unique_queries.append(q)
            seen.add(q)
            
    return unique_queries[:8]

    category = _get_product_category(topic, product_name)
    if category and category in PRODUCT_SEARCH_TERMS:
        queries.append(f"hand holding {category}")
        queries.append(f"{category} unboxing")
        queries.append(f"broken {category}")
        # Priority 3: All category visual terms (with 'holding' appended where possible, but we'll leave as is to be safe)
        queries.extend(PRODUCT_SEARCH_TERMS[category])
        print(f"   📦 Detected category: {category}")
        
    # Priority 4: Exact product name
    if product_name:
        queries.append(product_name.lower())
    
    # Priority 5: Raw generic tech terms to avoid clean studio shots
    if not queries:
        queries.extend(["hand holding phone", "broken phone screen", "phone unboxing desk"])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        q_lower = q.lower().strip()
        if q_lower and q_lower not in seen:
            seen.add(q_lower)
            unique_queries.append(q)
    
    return unique_queries


def fetch_background_clips(topic, product_name=None, num_clips=10):
    """
    Fetches background video clips from Pexels that match the content topic.
    Uses category-based search terms (NOT brand names) for relevance.
    """
    print(f"🎬 Fetching {num_clips} background clips...")
    print(f"   📝 Topic: {topic}")
    if product_name:
        print(f"   🏷️ Product: {product_name}")
    
    if not PEXELS_KEY:
        print("⚠️ PEXELS_API_KEY is not set.")
        return []

    headers = {"Authorization": PEXELS_KEY}
    clips_downloaded = []
    used_video_ids = set()  # Avoid duplicate videos
    
    # Build relevant search queries based on the product CATEGORY
    search_queries = _build_search_queries(topic, product_name or "")
    print(f"   🔍 Searches: {search_queries[:4]}")

    for sq in search_queries:
        if len(clips_downloaded) >= num_clips:
            break
        
        # How many more clips do we need?
        needed = num_clips - len(clips_downloaded)

        params = {"query": sq, "per_page": min(15, needed + 5), "orientation": "portrait", "size": "medium"}

        try:
            r = requests.get("https://api.pexels.com/videos/search",
                             headers=headers, params=params, timeout=10)
            if r.status_code != 200:
                print(f"   ⚠️ Search '{sq}' returned {r.status_code}")
                continue

            videos = r.json().get("videos", [])
            if not videos:
                print(f"   ⚠️ No videos for '{sq}'")
                continue

            for video in videos:
                if len(clips_downloaded) >= num_clips:
                    break
                
                # Skip duplicates
                video_id = video.get("id")
                if video_id in used_video_ids:
                    continue
                used_video_ids.add(video_id)

                # Find best resolution file (prefer 1080p)
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
                        print(f"   📥 Clip {len(clips_downloaded) + 1}/{num_clips} from '{sq}'")
                        data = requests.get(video_url, timeout=15).content
                        filename = f"bg_clip_{len(clips_downloaded)}.mp4"
                        with open(filename, "wb") as file:
                            file.write(data)
                        clips_downloaded.append(filename)
                    except Exception as e:
                        print(f"   ⚠️ Download error: {e}")

        except Exception as e:
            print(f"⚠️ Search '{sq}' failed: {e}")

    print(f"✅ Fetched {len(clips_downloaded)} clips matching topic.")
    return clips_downloaded
