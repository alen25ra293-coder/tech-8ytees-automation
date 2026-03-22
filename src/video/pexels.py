import os
import requests

PEXELS_KEY = os.environ.get("PEXELS_API_KEY")


def fetch_background_clips(topic, product_name=None, num_clips=12):
    """
    Fetches 10-15 background video clips from Pexels.
    Uses the specific product_name for relevance if available.
    """
    print(f"🎬 Fetching {num_clips} background clips for '{product_name or topic}'...")
    if not PEXELS_KEY:
        print("⚠️ PEXELS_API_KEY is not set.")
        return []

    # Extract clean search terms
    import re
    
    # If we have a specific product name, use it!
    if product_name and len(product_name) > 2:
        query = product_name
    else:
        clean_topic = re.sub(r'\$\d+', '', topic).lower()
        for stop_word in [" that ", " which ", " beats ", " rivals ", " replaces ", " can't "]:
            clean_topic = clean_topic.replace(stop_word, " ")
        
        # Remove common competitor names from the visual search
        for competitor in ["siri", "alexa", "google assistant", "airpods", "iphone", "macbook", "gopro"]:
            clean_topic = clean_topic.replace(competitor, " ")
            
        query = " ".join(clean_topic.split()[:3]).strip()

    if not query:
        query = "tech gadget"

    headers = {"Authorization": PEXELS_KEY}
    clips_downloaded = []

    # Search with multiple queries to get variety
    search_queries = [
        query,
        "modern tech desktop",
        "smartphone holding",
        "person holding gadget",
    ]

    for sq in search_queries:
        if len(clips_downloaded) >= num_clips:
            break

        params = {"query": sq, "per_page": 15, "orientation": "portrait", "size": "medium"}

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
                        print(f"   📥 Clip {len(clips_downloaded) + 1}/{num_clips}...")
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
