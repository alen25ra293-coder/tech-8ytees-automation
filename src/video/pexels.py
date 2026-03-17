import os
import requests

PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

def fetch_background_clips(topic, num_clips=4):
    """
    Fetches multiple background video clips from Pexels based on the topic.
    This creates a dynamic, multi-clip background.
    """
    print(f"🎬 Fetching {num_clips} background clips for '{topic}'...")
    if not PEXELS_KEY:
        print("⚠️ PEXELS_API_KEY is not set.")
        return []

    # Clean query to get broader results
    query = topic.split("vs")[0].replace("2026", "").strip()
    headers = {"Authorization": PEXELS_KEY}
    params = {"query": query, "per_page": 15, "orientation": "portrait", "size": "medium"}
    
    clips_downloaded = []
    
    try:
        r = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            print(f"⚠️ Pexels API returned {r.status_code}")
            return []
            
        videos = r.json().get("videos", [])
        
        for video in videos:
            if len(clips_downloaded) >= num_clips:
                break
                
            # Find the right resolution (close to 1080x1920 or best available)
            best_file = None
            for f in video["video_files"]:
                # Prefer 1080 width, or fallback
                if f.get("width") == 1080:
                    best_file = f
                    break
            
            # If no 1080 width, just take the first HD one
            if not best_file and len(video["video_files"]) > 0:
                best_file = sorted(video["video_files"], key=lambda x: x.get("width", 0), reverse=True)[0]
                
            if best_file:
                try:
                    video_url = best_file["link"]
                    print(f"   Downloading clip {len(clips_downloaded)+1}...")
                    data = requests.get(video_url, timeout=15).content
                    filename = f"bg_clip_{len(clips_downloaded)}.mp4"
                    with open(filename, "wb") as file:
                        file.write(data)
                    clips_downloaded.append(filename)
                except Exception as e:
                    print(f"   ⚠️ Error downloading a clip: {e}")
                    
        print(f"✅ Fetched {len(clips_downloaded)} distinct video clips.")
        return clips_downloaded

    except Exception as e:
        print(f"⚠️ Video fetch failed: {e}")
        return clips_downloaded
