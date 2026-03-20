import os
import random
import requests

PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

# ── High-energy FIRST CLIP queries ─────────────────────────────────────────
# These give visually explosive opening shots: hands unboxing, tech closeups,
# fast-moving product reveals. Always used for the VERY FIRST clip.
HIGH_ENERGY_FIRST_CLIPS = [
    "hands unboxing product closeup",
    "tech product macro closeup cinematic",
    "smartphone unboxing fast",
    "gadget reveal closeup hands",
    "product reveal cinematic macro",
]

# Product-focused visual aliases — avoids people/lifestyle shots
# Values describe what we want to SEE on screen (product shots, screens, abstract tech)
TOPIC_ALIAS_MAP = {
    "iphone": ["iphone unboxing closeup", "smartphone screen macro", "phone reveal cinematic"],
    "android": ["android phone unboxing", "smartphone product macro", "mobile closeup cinematic"],
    "laptop": ["laptop unboxing reveal", "laptop screen typing closeup", "laptop product macro"],
    "macbook": ["macbook unboxing product", "apple laptop screen close", "macbook typing fast"],
    "airpods": ["earbuds product macro", "airpods unboxing", "earbuds white background closeup"],
    "earbuds": ["earbuds unboxing reveal", "headphones product macro", "wireless earbuds cinematic"],
    "headphones": ["headphones product reveal", "headphones closeup macro", "studio headphones"],
    "vr":      ["vr headset unboxing", "virtual reality headset closeup", "vr product reveal"],
    "gaming":  ["gaming setup reveal", "gaming keyboard rgb closeup", "gaming mouse fast"],
    "ai":      ["artificial intelligence abstract", "digital code flowing screen", "neural network visualization"],
    "chatgpt": ["laptop screen code closeup", "typing fast keyboard", "screen interface close"],
    "smartwatch": ["smartwatch unboxing product", "watch screen closeup", "wearable tech cinematic"],
    "camera":  ["camera lens reveal", "photography equipment closeup", "video camera cinematic"],
    "drone":   ["drone unboxing product", "aerial footage", "drone product reveal"],
    "robot":   ["robot technology closeup", "robotic arm moving", "automation machine fast"],
    "budget":  ["product unboxing reveal", "gadget review table", "tech comparison fast"],
    "apple":   ["apple product unboxing", "iphone display reveal", "macbook screen open"],
    "samsung": ["samsung phone unboxing", "galaxy screen reveal", "android closeup cinematic"],
    "keyboard": ["mechanical keyboard rgb closeup", "keyboard typing fast", "keyboard product macro"],
    "mouse":   ["gaming mouse unboxing", "wireless mouse macro", "mouse product closeup"],
    "monitor": ["monitor screen reveal", "display product", "dual monitor setup cinematic"],
    "accessories": ["tech accessories closeup", "gadget unboxing hands", "cable product macro"],
    "charger": ["wireless charger product", "charging cable macro", "power adapter closeup"],
    "phone":   ["phone unboxing closeup", "smartphone reveal cinematic", "phone screen macro"],
    "tablet":  ["tablet unboxing reveal", "ipad product closeup", "screen tablet cinematic"],
    "speaker": ["speaker product reveal", "audio speaker closeup", "sound equipment macro"],
    "cable":   ["cable product macro", "tech cables closeup", "usb product cinematic"],
    "cheap":   ["product unboxing reveal", "gadget comparison fast", "value product macro"],
    "expensive": ["luxury product reveal", "premium gadget unboxing", "high end tech macro"],
    "wired":   ["wired headphones product", "cable audio macro", "jack plug closeup"],
    "wireless": ["wireless product reveal", "bluetooth device macro", "wireless tech cinematic"],
    "worst":   ["broken phone closeup", "tech fail product", "damaged gadget macro"],
    "regret":  ["returning product box", "unboxing mistake reveal", "gadget comparison"],
}

# Queries that always return product/screen footage (last-resort fallbacks)
SAFE_FALLBACK_QUERIES = [
    "technology product closeup",
    "gadget unboxing table",
    "smartphone screen white background",
    "circuit board technology",
]


def _build_search_queries(topic: str, first_clip_high_energy: bool = True) -> list:
    """
    Generate product-focused, no-people search queries from a topic.
    All queries are designed to return product shots, screens, and abstract tech visuals.
    If first_clip_high_energy=True, a random high-energy unboxing clip query is prepended
    to ensure the very first clip has visual impact.
    """
    import random
    topic_lower = topic.lower()
    queries = []

    # 0. First clip: always start with a visually explosive unboxing/reveal shot
    if first_clip_high_energy:
        queries.append(random.choice(HIGH_ENERGY_FIRST_CLIPS))

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
                        res_dl = requests.get(url, timeout=20)
                        res_dl.raise_for_status()
                        data = res_dl.content
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
