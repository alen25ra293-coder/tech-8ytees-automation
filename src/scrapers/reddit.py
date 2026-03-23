"""
Topic Scraper — NICHE: Budget Gadgets & Hidden Tech Gems Under $50
Fetches today's tech topic from RSS feeds, then rewrites through the
"cheap gadget beats expensive one" lens. Falls back to a curated niche list.

NOTE: Reddit scraping removed — Reddit blocks GitHub Actions IPs.
"""
import os
import requests
import random
import time
import xml.etree.ElementTree as ET
from google import genai

# ---------------------------------------------------------------------------
# Niche-specific fallback topics — budget gadgets & hidden gems
# ---------------------------------------------------------------------------
GADGET_TOPICS = [
    # Audio
    "$22 earbuds that rival $250 AirPods Pro noise cancelling",
    "$15 Bluetooth speaker that sounds like a $300 JBL Charge",
    "$30 gaming headset that beats $150 HyperX models",
    "$18 wireless earbuds with 40hr battery nobody talks about",
    "$25 bone conduction headphones that beat $130 Shokz",
    # Phone accessories
    "$20 phone camera lens kit that replaces $800 DSLR",
    "$12 wireless charger that beats $50 Apple MagSafe",
    "$18 magnetic phone mount better than any car mount",
    "$14 selfie stick tripod that every creator needs",
    "$8 screen protector that's better than $40 ones",
    # Desktop / Productivity
    "$10 USB-C hub that does what a $100 docking station does",
    "$35 keyboard that types better than $200 mechanicals",
    "$22 webcam that beats $100 Logitech models",
    "$20 desk lamp with wireless charging nobody knows about",
    "$8 cable organizer that fixes your messy desk forever",
    # Video / Cameras
    "$12 action camera that shoots 4K like a $400 GoPro",
    "$30 ring light that makes you look like a studio setup",
    "$25 mini projector that replaces your bedroom TV",
    "$15 portable monitor that turns your phone into a laptop",
    # Smart Home
    "$28 smart plug that cuts your electricity bill in half",
    "$18 LED strip lights that transform any room instantly",
    "$15 Smart TV remote that controls everything in your house",
    "$20 smart bulbs cheaper and better than Philips Hue",
    # Portable / Travel
    "$30 power bank that charges 3 devices simultaneously",
    "$35 handheld fan that's basically portable AC",
    "$10 screen cleaner kit that brings old screens back to life",
    "$28 portable SSD faster than most laptop internal drives",
    "$25 travel adapter that works in every country",
    # Random hidden gems
    "$15 thermal phone case that stops overheating",
    "$20 Bluetooth tracker that beats $30 AirTag",
    "$22 portable Bluetooth printer for instant photos",
    "$12 phone cooling fan for gaming that actually works",
    "$18 mini vacuum cleaner for your keyboard and desk",
    "$25 smart water bottle that reminds you to drink",
]


# ── RSS Feed URLs ─────────────────────────────────────────────────────────────
RSS_FEEDS = [
    "https://hnrss.org/frontpage?count=30",          # Hacker News front page
    "https://feeds.feedburner.com/TechCrunch/",      # TechCrunch
    "https://www.wired.com/feed/rss",                # Wired
    "https://www.theverge.com/rss/index.xml",        # The Verge
    "https://arstechnica.com/feed/",                 # Ars Technica
]

# Words that indicate non-viral / non-video-friendly topics
_SKIP_WORDS = {
    "thread", "weekly", "discussion", "ask hn", "show hn",
    "hiring", "who is hiring", "launch hn", "tell hn",
    "podcast", "newsletter", "roundup", "summary",
    "fundraise", "acqui", "ipo", "earnings",
    "obituary", "rip:", "passed away",
}

# Topics to explicitly ignore from RSS (for noise reduction)
IGNORE_KEYWORDS = {
    "student", "school", "politics", "war", "celebrity", "dating", "attractive",
    "who is hiring", "launch hn", "tell hn",
    "podcast", "newsletter", "roundup", "summary",
    "fundraise", "acqui", "ipo", "earnings",
    "obituary", "rip:", "passed away",
}


def get_trending_topics_rss() -> list[str]:
    """
    Fetch top posts from tech RSS feeds and return as topic strings.
    Filters out boring or non-video-friendly titles.
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

            root = ET.fromstring(resp.content)

            # Handle both RSS and Atom formats
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for item in items[:15]:
                title_elem = item.find("title")
                if title_elem is None:
                    title_elem = item.find("{http://www.w3.org/2005/Atom}title")

                if title_elem is None or not title_elem.text:
                    continue

                title = title_elem.text.strip()

                # Filter out low-quality / non-viral titles
                if filter_rss_topic(title):
                    trending.append(title)

        except Exception as e:
            print(f"   ⚠️ RSS feed failed ({feed_url[:30]}...): {e}")
            continue

    if trending:
        print(f"✅ Found {len(trending)} trending topics from RSS feeds.")
        return trending[:20]

    print("⚠️  RSS feeds unavailable or returned no usable posts.")
    return []


def filter_rss_topic(topic: str) -> bool:
    """Returns True if the topic sounds like a valid tech/gadget news item."""
    if not topic or len(topic) < 15:
        return False

    t_lower = topic.lower()

    # Check for ignore keywords
    if any(k in t_lower for k in IGNORE_KEYWORDS):
        return False

    tech_keywords = {
        "gadget", "tech", "iphone", "samsung", "nvidia", "ai", "apple", "google",
        "amazon", "review", "launch", "release", "leak", "gpu", "cpu", "laptop",
        "keyboard", "setup", "budget", "find", "hidden", "gem", "deal",
        "earbuds", "speaker", "headset", "wireless", "phone", "charger", "mount",
        "selfie", "screen protector", "usb-c", "webcam", "desk lamp", "cable organizer",
        "action camera", "ring light", "projector", "monitor", "smart plug", "led strip",
        "smart tv", "smart bulb", "power bank", "fan", "cleaner", "ssd", "travel adapter",
        "thermal", "bluetooth tracker", "printer", "cooling fan", "vacuum cleaner", "water bottle",
        "edc", "everyday carry", "retro gaming", "minimalist", "car tech", "charging solution",
    }
    return any(k in t_lower for k in tech_keywords)


def _rewrite_topic_viral(topic: str) -> str:
    """
    Use Gemini to turn a dry news headline into a budget gadget viral angle.
    Falls back to original topic if Gemini is unavailable.
    """
    try:
        from google import genai

        keys_raw = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
        keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
        if not keys:
            return topic

        client = genai.Client(api_key=random.choice(keys))

        prompt = f"""Rewrite this tech headline into a viral SHORT title — NICHE: budget gadgets & hidden tech gems under $50.

Original headline: "{topic}"

Rules:
- Output ONE line only — the rewritten topic (no quotes, no commentary)
- Frame it as "This $[low price] [gadget] does what your $[high price] [brand product] can't"
- Must include a specific dollar amount ($15, $22, $30 etc) and name an expensive product it beats
- Max 60 characters
- Curiosity gap or bold claim — make the viewer stop scrolling
- Examples:
  "Apple announces AirPods 4" → "$22 earbuds that destroyed my $250 AirPods"
  "Samsung launches new camera phone" → "$20 lens kit that replaces $800 DSLR shots"
  "New smart home hub released" → "$28 smart plug that cut my electricity bill in half"
  "GoPro Hero 13 review" → "$12 action camera that shoots like a $400 GoPro"
"""
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        rewritten = resp.text.strip().strip('"').strip("'")
        if rewritten and len(rewritten) > 10:
            print(f'   🔄 Rewrote: "{topic[:40]}..." → "{rewritten}"')
            return rewritten
    except Exception:
        pass

    return topic


def get_todays_topic() -> str:
    """
    Pick today's topic.
    Prefers RSS trending topics (rewritten for virality); falls back to curated list.
    Uses true randomness so each run picks a unique topic.
    """
    trending = get_trending_topics_rss()

    if trending:
        # Pick a random trending topic and rewrite it for viral phrasing
        topic = random.choice(trending)
        topic = _rewrite_topic_viral(topic)
        print(f"📌 Today's trending topic: {topic}")
    else:
        topic = random.choice(GADGET_TOPICS)
        print(f"📌 Today's fallback topic: {topic}")

    return topic
