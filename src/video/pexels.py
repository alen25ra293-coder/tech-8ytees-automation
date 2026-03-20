import os
import random
import requests

PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

# Visual search aliases — broader synonyms for common tech topics
# so Pexels finds interesting, diverse footage even for niche subjects
TOPIC_ALIAS_MAP = {
    "iphone": ["smartphone", "mobile phone", "technology"],
    "android": ["smartphone", "mobile", "app"],
    "laptop": ["computer", "workspace", "office tech"],
    "macbook": ["laptop", "computer", "workspace"],
    "airpods": ["earbuds", "headphones", "wireless audio"],
    "earbuds": ["headphones", "audio", "music"],
    "headphones": ["audio", "music", "studio"],
    "vr": ["virtual reality", "gaming", "futuristic tech"],
    "gaming": ["video game", "gaming setup", "esports"],
    "ai": ["artificial intelligence", "robot", "future tech"],
    "chatgpt": ["artificial intelligence", "computer", "technology"],
    "smartwatch": ["wearable", "fitness tracker", "watch"],
    "camera": ["photography", "video production", "lens"],
    "projector": ["cinema", "home theater", "movie"],
    "smart home": ["home automation", "technology home", "modern home"],
    "keyboard": ["computer setup", "desk setup", "typing"],
    "mouse": ["computer accessories", "desk setup", "gaming"],
    "monitor": ["display", "screen setup", "desk"],
    "usb": ["cable", "tech accessories", "computer"],
    "charger": ["wireless charging", "power", "phone accessories"],
    "drone": ["aerial", "flying", "drone footage"],
    "robot": ["robotics", "automation", "technology"],
    "electric": ["electric vehicle", "battery", "technology"],
}


def _build_search_queries(topic: str) -> list[str]:
    """Generate several search queries from a topic for varied clip results."""
    topic_lower = topic.lower()
    queries = []

    # Try alias-based broad queries first
    for key, aliases in TOPIC_ALIAS_MAP.items():
        if key in topic_lower:
            queries.extend(aliases)
            break

    # Always add keyword extracts from the topic itself
    words = [w for w in topic.split() if len(w) > 4 and w.lower() not in
             {"that", "this", "with", "from", "about", "which", "their", "every",
              "beats", "heres", "nobod", "secre", "actua", "finally"}]
    if words:
        queries.append(" ".join(words[:3]))  # first 3 meaningful words
        queries.append(words[0])              # just the main noun

    # Generic tech fallbacks
    queries += ["technology gadget", "tech product", "modern technology", "digital innovation"]

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
