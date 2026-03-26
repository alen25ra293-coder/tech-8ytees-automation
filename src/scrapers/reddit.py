"""
Topic Scraper — NICHE: Budget Gadgets & Hidden Tech Gems Under ₹2000 / $25
Fetches today's tech topic from RSS feeds, then rewrites through the
"cheap gadget beats expensive one" lens. Falls back to a curated niche list.
Includes deduplication: topics already used are skipped.

NOTE: Reddit scraping removed — Reddit blocks GitHub Actions IPs.
"""
import os
import requests
import random
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Niche-specific fallback topics — budget gadgets & hidden gems
# ---------------------------------------------------------------------------
GADGET_TOPICS = [
    # Audio — Indian ₹ pricing
    "₹1,799 earbuds with noise cancelling that rivals ₹20,000 AirPods Pro",
    "₹999 Bluetooth speaker that sounds like a ₹8,000 JBL Charge",
    "₹1,499 gaming headset that beats ₹5,000 HyperX Cloud",
    "₹800 wireless earbuds with 40hr battery nobody talks about",
    "₹1,299 bone conduction headphones that beat ₹9,000 Shokz",
    "₹999 open-ear earbuds that let you hear your surroundings",
    # Phone accessories
    "₹999 phone camera lens kit that replaces a ₹50,000 DSLR",
    "₹499 wireless charger faster than ₹3,500 Apple MagSafe",
    "₹699 magnetic phone mount that beats every car mount",
    "₹399 selfie stick tripod every creator needs under ₹500",
    "₹299 screen protector better than ₹1,200 branded ones",
    "₹599 phone cooling fan for gaming that actually works",
    "₹799 foldable phone stand better than ₹2,500 premium stands",
    # Desktop / Productivity
    "₹999 USB-C hub that does what a ₹6,000 docking station does",
    "₹1,799 keyboard that types better than ₹12,000 mechanicals",
    "₹1,299 webcam that beats ₹7,000 Logitech C920",
    "₹899 desk lamp with wireless charging nobody knows about",
    "₹299 cable organizer that fixes your messy desk forever",
    "₹799 ergonomic mouse that beats ₹5,000 Logitech MX Master",
    # Video / Cameras
    "₹1,499 action camera that shoots 4K like a ₹30,000 GoPro",
    "₹1,999 ring light that makes you look like a studio setup",
    "₹2,499 mini projector that replaces your bedroom TV",
    "₹1,699 portable monitor that turns your tablet into a laptop",
    "₹999 smartphone microphone that records studio-quality audio",
    # Smart Home
    "₹699 smart plug that cuts your electricity bill in half",
    "₹499 LED strip lights that transform any room instantly",
    "₹799 smart bulb cheaper and better than Philips Hue",
    "₹999 smart IR remote that controls every device at home",
    "₹1,499 robot vacuum cleaner under ₹1,500 that actually works",
    # Portable / Travel
    "₹1,299 power bank that charges 3 devices at 65W",
    "₹999 handheld fan that's basically portable AC",
    "₹1,999 portable SSD faster than most laptop internal drives",
    "₹599 Bluetooth tracker that beats ₹3,500 AirTag",
    "₹799 travel adapter with 4 USB ports for every country",
    # Hidden gems
    "₹699 mini thermal printer for instant sticker photos",
    "₹499 mini vacuum cleaner for keyboard and desk",
    "₹799 smart water bottle with hydration reminders",
    "₹1,299 lap desk with built-in wireless charger",
    "₹599 magnetic cable organizer that keeps your desk perfect",
    "₹1,199 folding keyboard that fits in your pocket",
    "₹899 UV sanitizer box that kills phone germs in 3 minutes",
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
    Use Gemini to turn a dry news headline into a budget gadget viral angle.
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
        resp = model.generate_content(prompt)
        rewritten = resp.text.strip().strip('"').strip("'")
        if rewritten and len(rewritten) > 10:
            print(f'   🔄 Rewrote: "{topic[:40]}..." → "{rewritten}"')
            return rewritten
    except Exception:
        pass

    return topic


def _load_used_set() -> set:
    """Load the set of previously used topics from used_topics.json."""
    used_file = "used_topics.json"
    if not os.path.exists(used_file):
        return set()
    try:
        import json
        with open(used_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("topics", []))
    except Exception:
        return set()


def _topic_is_used(topic: str, used: set) -> bool:
    """Check if topic or a close variant has already been used."""
    t = topic.strip().lower()
    if t in used:
        return True
    words = t.split()
    for i in range(max(0, len(words) - 3)):
        chunk = " ".join(words[i:i+4])
        if any(chunk in u for u in used):
            return True
    return False


def mark_topic_used(topic: str):
    """Persist a topic to used_topics.json to prevent future repetition."""
    import json
    used_file = "used_topics.json"
    used = _load_used_set()
    used.add(topic.strip().lower())
    try:
        with open(used_file, "w", encoding="utf-8") as f:
            json.dump({"topics": sorted(used)}, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save used_topics.json: {e}")


def get_todays_topic() -> str:
    """
    Pick today's topic.
    Prefers RSS trending topics (rewritten for virality); falls back to curated list.
    Deduplicates against used_topics.json.
    """
    used = _load_used_set()
    trending = get_trending_topics_rss()

    if trending:
        # Filter out already-used topics
        fresh_trending = [t for t in trending if not _topic_is_used(t, used)]
        pool = fresh_trending if fresh_trending else trending
        topic = random.choice(pool)
        topic = _rewrite_topic_viral(topic)
        print(f"📌 Today's trending topic: {topic}")
    else:
        fresh_curated = [t for t in GADGET_TOPICS if not _topic_is_used(t, used)]
        if not fresh_curated:
            print("⚠️  All curated topics used — resetting pool.")
            fresh_curated = GADGET_TOPICS
        topic = random.choice(fresh_curated)
        print(f"📌 Today's fallback topic: {topic}")

    return topic
