import requests
import random
from datetime import date

GADGET_TOPICS = [
    "budget smartphone vs flagship 2026",
    "best wireless earbuds under $50 2026",
    "smartwatch Apple Watch vs Samsung Galaxy 2026",
    "best budget laptop under $500 2026",
    "USB-C hub you didn't know you needed 2026",
    "robot vacuum comparison Roomba vs Roborock 2026",
    "best mechanical keyboard under $100 2026",
    "portable charger power bank comparison 2026",
    "smart home gadgets worth buying 2026",
    "gaming mouse comparison 2026",
    "best webcam for streaming 2026",
    "noise cancelling headphones budget vs premium 2026",
    "hidden iPhone features nobody talks about 2026",
    "best AI gadgets of 2026",
]

def get_trending_topics_reddit():
    try:
        print("📱 Fetching trending topics from Reddit...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        subreddits = ['technology', 'gadgets', 'tech']
        trending = []
        
        for subreddit in subreddits:
            try:
                url = f'https://www.reddit.com/r/{subreddit}/hot.json?limit=25'
                r = requests.get(url, headers=headers, timeout=10)
                
                if r.status_code == 200:
                    data = r.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        title = post.get('data', {}).get('title', '').strip()
                        if title and 20 < len(title) < 150 and 'thread' not in title.lower():
                            trending.append(title)
                    
                    if len(trending) >= 10:
                        break
            except Exception:
                continue
        
        if trending:
            print(f"✅ Found {len(trending)} trending topics from Reddit")
            return trending[:15]
        else:
            print(f"⚠️ Reddit fetch returned no posts")
            
    except Exception as e:
        print(f"⚠️ Reddit fetch failed ({type(e).__name__})")
    
    return []

def get_todays_topic():
    trending = get_trending_topics_reddit()
    
    if trending:
        random.seed(date.today().toordinal())
        topic = random.choice(trending)
        print(f"📌 Today's trending topic: {topic}")
        return topic
    else:
        random.seed(date.today().toordinal())
        topic = random.choice(GADGET_TOPICS)
        print(f"📌 Today's fallback topic: {topic}")
        return topic
