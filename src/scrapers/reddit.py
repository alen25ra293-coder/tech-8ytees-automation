"""
Topic Scraper
Fetches today's hottest tech topic from RSS feeds (Hacker News, TechCrunch, Wired),
falling back to a large curated list if RSS is unavailable.

Includes AI-powered topic rewriting to turn dry headlines into viral angles.

NOTE: Reddit scraping was removed because Reddit blocks GitHub Actions IPs.
"""
import os
import requests
import random
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Large curated fallback list — diverse tech topics, viral phrasing
# ---------------------------------------------------------------------------
GADGET_TOPICS = [
    # AI — high CTR category
    "The AI tool that replaces your entire team",
    "ChatGPT is dying — this AI is taking over",
    "The free AI that beats Midjourney",
    "AI gadgets nobody is talking about in 2026",
    "This AI tool made me $500 in one week",
    "Why everyone is quitting ChatGPT for this",
    "Best free AI tools you need right now",
    "Google AI just destroyed the competition",
    "The AI app that does your homework in 10 seconds",
    "I replaced my assistant with a free AI tool",
    # Smartphones — highest volume
    "Stop buying iPhones — here's why",
    "Hidden iPhone features that feel illegal to know",
    "The Android phone that beats iPhone for half the price",
    "Samsung Galaxy vs iPhone — one clear winner",
    "The budget phone pros secretly use",
    "Best smartphones under $200 in 2026",
    "Why I switched from iPhone to Android",
    "The phone camera trick nobody tells you",
    "Your phone is spying on you — here's the proof",
    "The phone setting you NEED to turn off right now",
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
    "The $50 gaming gear that pros actually use",
    # Accessories & Gadgets
    "The USB-C hub that changes your whole setup",
    "This $30 gadget went viral for a reason",
    "The $50 gadget that embarrasses your laptop",
    "Best tech accessories nobody talks about",
    "The gadget I wish I bought years ago",
    "Don't buy a webcam until you watch this",
    "The best desk setup upgrades under $100",
    "The mini projector that replaces your TV",
    # Wearables
    "Best budget smartwatch that beats Apple Watch",
    "The fitness tracker that changed my life",
    "Why smart glasses are finally worth it",
    "The smartwatch Apple doesn't want you to see",
    # Software & Apps
    "The FREE software that replaces paid apps",
    "Best free apps that feel too good to be free",
    "The browser extension everyone should have",
    "The free tool that saves me 2 hours daily",
    "Delete these apps from your phone RIGHT NOW",
    # VR / Future Tech
    "The VR headset nobody is talking about",
    "Why everyone is wrong about VR",
    "The craziest AI gadgets of 2026",
    "The tech that will replace your smartphone",
    "Why foldable phones are the future",
    "The battery tech that changes everything",
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
                title_lower = title.lower()
                if (
                    title
                    and 15 < len(title) < 150
                    and not any(skip in title_lower for skip in _SKIP_WORDS)
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


def _rewrite_topic_viral(topic: str) -> str:
    """
    Use Gemini to turn a dry news headline into a viral video angle.
    Falls back to original topic if Gemini is unavailable.
    """
    try:
        import google.generativeai as genai

        keys_raw = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
        keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
        if not keys:
            return topic

        genai.configure(api_key=random.choice(keys))
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""Rewrite this tech news headline into a viral YouTube Shorts title angle.

Original headline: "{topic}"

Rules:
- Output ONE line only — the rewritten topic (no quotes, no commentary)
- Use emotional triggers: "Nobody Talks About", "The Truth About", "Why I Stopped", "$30 Alternative"
- Make it a curiosity gap or a bold claim
- Max 60 characters
- Include a specific hook: a dollar amount, a brand name, or a bold opinion
- Examples of good rewrites:
  "Apple announces M4 chip" → "Why the M4 Mac is a waste of money"
  "Samsung Galaxy S25 review" → "The $800 phone that can't beat a $300 one"
  "OpenAI releases GPT-5" → "GPT-5 just killed 3 apps you pay for"
"""
        resp = model.generate_content(prompt)
        rewritten = resp.text.strip().strip('"').strip("'")
        if rewritten and len(rewritten) > 10:
            print(f"   🔄 Rewrote: \"{topic[:40]}...\" → \"{rewritten}\"")
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
