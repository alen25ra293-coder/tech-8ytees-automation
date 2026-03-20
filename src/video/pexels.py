import os
import random
import requests

PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

# Product-focused visual aliases — avoids people/lifestyle shots
# Values describe what we want to SEE on screen (product shots, screens, abstract tech)
TOPIC_ALIAS_MAP = {
    "iphone": ["iphone product shot", "smartphone screen closeup", "phone unboxing"],
    "android": ["android phone", "smartphone product", "mobile phone closeup"],
    "laptop": ["laptop screen closeup", "typing laptop", "computer screen workspace"],
    "macbook": ["macbook product shot", "laptop screen", "apple computer"],
    "airpods": ["earbuds product shot", "headphones closeup", "audio tech"],
    "earbuds": ["earbuds white background", "headphones product", "wireless earbuds"],
    "headphones": ["headphones product shot", "audio tech closeup", "studio headphones"],
    "vr":      ["vr headset product", "virtual reality headset closeup", "futuristic headset"],
    "gaming":  ["gaming setup no people", "gaming keyboard mouse", "gaming monitor screen"],
    "ai":      ["artificial intelligence visualization", "digital code screen", "neural network abstract"],
    "chatgpt": ["computer screen code", "ai interface screen", "tech laptop screen"],
    "smartwatch": ["smartwatch product shot", "wearable tech closeup", "watch screen"],
    "camera":  ["camera lens product", "photography equipment", "video camera"],
    "projector": ["projector tech", "projection screen", "home theater setup"],
    "smart home": ["smart home device", "home automation gadget", "modern router"],
    "keyboard": ["keyboard product shot", "mechanical keyboard closeup", "typing keys"],
    "mouse":   ["computer mouse product", "wireless mouse closeup", "gaming mouse"],
    "monitor": ["computer monitor closeup", "display screen", "dual monitor setup"],
    "usb":     ["cable technology", "usb hub product", "tech accessories table"],
    "charger": ["wireless charger product", "charging phone", "power adapter"],
    "drone":   ["drone product shot", "aerial drone", "drone footage sky"],
    "robot":   ["robot technology", "robotic arm", "automation machine"],
    "electric": ["electric vehicle tech", "battery technology", "circuit board"],
    "budget":  ["budget gadget review", "unboxing product", "tech comparison"],
    "apple":   ["apple product shot", "iphone display", "macbook screen"],
    "samsung": ["samsung phone product", "galaxy screen", "android closeup"],
}

# Queries that always return product/screen footage (last-resort fallbacks)
SAFE_FALLBACK_QUERIES = [
    "technology product closeup",
    "gadget unboxing table",
    "smartphone screen white background",
    "circuit board technology",
    "digital screen abstract",
    "tech desk setup",
]


def _build_search_queries(topic: str) -> list:
    """
    Generate product-focused, no-people search queries from a topic.
    All queries are designed to return product shots, screens, and abstract tech visuals.
    """
    topic_lower = topic.lower()
    queries = []

    # 1. Alias-based queries (product-focused visuals for known topics)
    for key, aliases in TOPIC_ALIAS_MAP.items():
        if key in topic_lower:
            queries.extend(aliases)
            break

    # 2. Topic keywords + "product technology" suffix (avoids lifestyle shots)
    words = [w for w in topic.split() if len(w) > 4 and w.lower() not in
             {"that", "this", "with", "from", "about", "which", "their",
              "every", "beats", "nobod", "secre", "actua", "heres", "finall"}]
    if words:
        # Append "product" / "tech" to push Pexels toward product shots
        queries.append(f"{words[0]} product technology")
        queries.append(f"{words[0]} closeup screen")

    # 3. Always add safe fallbacks at the end
    queries.extend(SAFE_FALLBACK_QUERIES[:3])

    return queries


def fetch_background_clips(topic: str, num_clips: int = 5) -> list[str]:
    """
    Fetches varied background video clips from Pexels.
    - Uses randomized page selection for different clips each run
    - Tries multiple search queries for visual variety
    - Returns up to num_clips unique downloaded clips
    """
    print(f"🎬 Fetching {num_clips} background clips for '{topic}'...")
    if not PEXELS_KEY:
        print("⚠️ PEXELS_API_KEY not set — no background clips.")
        return []

    headers = {"Authorization": PEXELS_KEY}
    clips_downloaded: list[str] = []
    used_video_ids: set[int] = set()

    queries = _build_search_queries(topic)

    for query in queries:
        if len(clips_downloaded) >= num_clips:
            break

        # Randomize page so we never get the exact same set of clips
        page = random.randint(1, 5)
        per_page = 15

        try:
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers=headers,
                params={
                    "query": query,
                    "per_page": per_page,
                    "page": page,
                    "orientation": "portrait",
                    "size": "medium",
                },
                timeout=10,
            )
            if r.status_code != 200:
                continue

            videos = r.json().get("videos", [])
            # Shuffle to further randomize which clips we pick
            random.shuffle(videos)

            for video in videos:
                if len(clips_downloaded) >= num_clips:
                    break

                vid_id = video.get("id", 0)
                if vid_id in used_video_ids:
                    continue
                used_video_ids.add(vid_id)

                # Prefer portrait (1080 wide), else take highest-res available
                best_file = None
                for vf in video.get("video_files", []):
                    if vf.get("width") == 1080:
                        best_file = vf
                        break
                if not best_file:
                    files = video.get("video_files", [])
                    if files:
                        best_file = sorted(files, key=lambda x: x.get("width", 0), reverse=True)[0]

                if best_file:
                    try:
                        url = best_file["link"]
                        n = len(clips_downloaded)
                        print(f"   Downloading clip {n + 1} ({query})...")
                        data = requests.get(url, timeout=20).content
                        fname = f"bg_clip_{n}.mp4"
                        with open(fname, "wb") as f:
                            f.write(data)
                        clips_downloaded.append(fname)
                    except Exception as e:
                        print(f"   ⚠️ Clip download error: {e}")

        except Exception as e:
            print(f"⚠️ Pexels search failed for query '{query}': {e}")

    if clips_downloaded:
        print(f"✅ Fetched {len(clips_downloaded)} distinct video clips.")
    else:
        print("⚠️ No clips downloaded — video will use dark fallback background.")

    return clips_downloaded
