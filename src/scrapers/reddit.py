"""
Topic Scraper
Fetches today's hottest tech topic from RSS feeds (Hacker News, TechCrunch, Wired),
falling back to a large curated list if RSS is unavailable.

NOTE: Reddit scraping was removed because Reddit blocks GitHub Actions IPs.
"""
import requests
import random
import xml.etree.ElementTree as ET
from datetime import datetime

# ---------------------------------------------------------------------------
# Large curated fallback list — diverse tech topics for maximum variety
# ---------------------------------------------------------------------------
GADGET_TOPICS = [
    # AI
    "The AI tool that replaces your entire team",
    "ChatGPT is dying — this AI is taking over",
    "The free AI that beats Midjourney",
    "AI gadgets nobody is talking about in 2026",
    "This AI tool made me $500 in one week",
    "Why everyone is quitting ChatGPT for this",
    "Best free AI tools you need right now",
    "Google AI just destroyed the competition",
    # Smartphones
    "Stop buying iPhones — here's why",
    "Hidden iPhone features that feel illegal to know",
    "The Android phone that beats iPhone for half the price",
    "Samsung Galaxy vs iPhone — one clear winner",
    "The budget phone pros secretly use",
    "Best smartphones under $200 in 2026",
    "Why I switched from iPhone to Android",
    "The phone camera trick nobody tells you",
    # Laptops & PCs
    "The $400 laptop that embarrasses MacBook",
    "Budget laptop that outperforms expensive ones",
    "Why you don't need an M4 Mac",
    "The Windows laptop that finally beats Apple",
    "Best budget laptop for students in 2026",
    "This laptop changed how I work forever",
    "The mini PC that replaces a gaming tower",
    "Why I returned my MacBook Pro",
    # Audio
    "Stop buying AirPods — here's why",
    "The $30 earbuds that beat AirPods Pro",
    "Best budget wireless earbuds of 2026",
    "The gaming headset audiophiles secretly love",
    "Why premium headphones are a scam",
    "I tested 7 earbuds — only one is worth it",
    "The noise cancelling earbuds nobody talks about",
    # Smart Home
    "Smart home gadgets that actually save money",
    "The smart home setup nobody tells you about",
    "AI home gadgets that actually spy on you",
    "Best smart home devices for $50 or less",
    "Why I removed all my smart home devices",
    "The smart plug that cut my electricity bill",
    "Google Home vs Amazon Alexa — truth exposed",
    # Gaming
    "The gaming mouse pros secretly use",
    "Why PC gaming is cheaper than you think",
    "The budget gaming setup that beats PS5",
    "Best gaming monitor for the money in 2026",
    "Why I quit console gaming for PC",
    "The mechanical keyboard that changed everything",
    "Mechanical keyboards are a luxury scam",
    # Accessories & Gadgets
    "The USB-C hub that changes your whole setup",
    "This $30 gadget went viral for a reason",
    "The $50 gadget that embarrasses your laptop",
    "Best tech accessories nobody talks about",
    "The gadget I wish I bought years ago",
    "Don't buy a webcam until you watch this",
    "The best desk setup upgrades under $100",
    "The mini projector that replaces your TV",
    # Cameras & Photography
    "The camera phone that beats your DSLR",
    "Best camera for YouTube under $500",
    "Why I stopped using a real camera",
    "The GoPro killer nobody is talking about",
    "Best action camera of 2026 ranked",
    # Wearables
    "Best budget smartwatch that beats Apple Watch",
    "The fitness tracker that changed my life",
    "Roborock vs Roomba — one wins, one fails",
    "Why smart glasses are finally worth it",
    "The smartwatch Apple doesn't want you to see",
    # Software & Apps
    "The FREE software that replaces paid apps",
    "Best free apps that feel too good to be free",
    "The browser extension everyone should have",
    "Why I use Linux and never looked back",
    "The free tool that saves me 2 hours daily",
    # VR / Future Tech
    "The VR headset nobody is talking about",
    "Why everyone is wrong about VR",
    "The craziest AI gadgets of 2026",
    "Best wireless charger for any phone",
    "The tech that will replace your smartphone",
    "Why foldable phones are the future",
    "The battery tech that changes everything",
    "Electric gadgets that pay for themselves",
]


# ── RSS Feed URLs (these don't block GitHub Actions IPs) ──────────────────────
RSS_FEEDS = [
    "https://hnrss.org/frontpage?count=30",          # Hacker News front page
    "https://feeds.feedburner.com/TechCrunch/",      # TechCrunch
    "https://www.wired.com/feed/rss",                # Wired
    "https://www.theverge.com/rss/index.xml",        # The Verge
    "https://arstechnica.com/feed/",                 # Ars Technica
]


def get_trending_topics_rss() -> list[str]:
    """
    Fetch top posts from tech RSS feeds and return as topic strings.
    """
    print("📱 Fetching trending topics from RSS feeds...")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml",
    }

    trending: list[str] = []

    for feed_url in RSS_FEEDS:
        if len(trending) >= 20:
            break
        try:
            resp = requests.get(feed_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                continue
            
            # Parse RSS/Atom XML
            root = ET.fromstring(resp.content)
            
            # Handle both RSS and Atom formats
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
            
            for item in items[:15]:
                # RSS format: <title>
                title_elem = item.find("title")
                if title_elem is None:
                    # Atom format: <title>
                    title_elem = item.find("{http://www.w3.org/2005/Atom}title")
                
                if title_elem is None or not title_elem.text:
                    continue
                    
                title = title_elem.text.strip()
                
                # Filter out low-quality titles
                if (
                    title
                    and 15 < len(title) < 150
                    and "thread" not in title.lower()
                    and "weekly" not in title.lower()
                    and "discussion" not in title.lower()
                    and "ask hn" not in title.lower()
                    and "show hn" not in title.lower()
                ):
                    trending.append(title)
                    
        except Exception as e:
            print(f"   ⚠️ RSS feed failed ({feed_url[:30]}...): {e}")
            continue

    if trending:
        print(f"✅ Found {len(trending)} trending topics from RSS feeds.")
        return trending[:20]

    print("⚠️  RSS feeds unavailable or returned no usable posts.")
    return []


def get_todays_topic() -> str:
    """
    Pick today's topic.
    Prefers RSS trending topics; falls back to the large curated local list.
    Uses current timestamp (not just date) so EVERY run picks a different topic.
    """
    trending = get_trending_topics_rss()

    # Use current minute-level timestamp so each run (7AM and 7PM) picks a different topic
    seed = int(datetime.now().timestamp() // 60)  # changes every minute
    random.seed(seed)

    if trending:
        topic = random.choice(trending)
        print(f"📌 Today's trending topic: {topic}")
    else:
        topic = random.choice(GADGET_TOPICS)
        print(f"📌 Today's fallback topic: {topic}")

    return topic
