"""
Reddit Topic Scraper
Fetches today's hottest tech topic from Reddit,
falling back to a curated local list if Reddit is unavailable.
"""
import requests
import random
from datetime import date

# ---------------------------------------------------------------------------
# Curated fallback topics — viral-style titles optimised for Shorts hooks
# ---------------------------------------------------------------------------
GADGET_TOPICS = [
    "The $50 gadget that embarrasses your laptop",
    "Stop buying AirPods — here's why",
    "Hidden iPhone features that feel illegal to know",
    "The USB-C hub that changes your whole setup",
    "Roborock vs Roomba — one wins, one fails",
    "Mechanical keyboards are a luxury scam",
    "The smartphone battery lie everyone believes",
    "AI home gadgets that actually spy on you",
    "The gaming mouse pros secretly use",
    "Don't buy a webcam until you watch this",
    "The craziest AI gadgets of 2026",
    "Best budget smartwatch that beats Apple Watch",
    "The FREE software that replaces paid apps",
    "This $30 gadget went viral for a reason",
    "The gaming headset audiophiles secretly love",
    "Budget laptop that outperforms expensive ones",
    "The VR headset nobody is talking about",
    "Smart home gadgets that actually save money",
    "Best wireless charger for any phone",
    "The mini projector that replaces your TV",
]

# ── Reddit scraper ──────────────────────────────────────
SUBREDDITS = ["gadgets", "technology", "tech", "pcmasterrace", "futurology", "artificial"]


def get_trending_topics_reddit() -> list[str]:
    """
    Fetch top posts from tech subreddits and return as topic strings.
    """
    print("📱 Fetching trending topics from Reddit...")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    trending: list[str] = []

    for sub in SUBREDDITS:
        if len(trending) >= 15:
            break
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=25&t=day"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            posts = resp.json().get("data", {}).get("children", [])
            for post in posts:
                title = post.get("data", {}).get("title", "").strip()
                # Filter out low-quality titles
                if (
                    title
                    and 20 < len(title) < 150
                    and "thread" not in title.lower()
                    and "weekly" not in title.lower()
                    and "discussion" not in title.lower()
                ):
                    trending.append(title)
        except Exception:
            continue

    if trending:
        print(f"✅ Found {len(trending)} trending topics from Reddit.")
        return trending[:15]

    print("⚠️  Reddit unavailable or returned no usable posts.")
    return []


def get_todays_topic() -> str:
    """
    Pick today's topic.
    Prefers Reddit trending topics; falls back to the curated local list.
    Uses date-seeded randomness so the same topic is picked if script is re-run today.
    """
    trending = get_trending_topics_reddit()

    random.seed(date.today().toordinal())

    if trending:
        topic = random.choice(trending)
        print(f"📌 Today's trending topic: {topic}")
    else:
        topic = random.choice(GADGET_TOPICS)
        print(f"📌 Today's fallback topic: {topic}")

    return topic
