# scripts/test_feeds.py
import requests
import feedparser
import yaml
from pathlib import Path

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; ACW-Bot/1.0)",
})

def test_feed(url):
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.text)
            if feed.entries:
                return f"✅ {len(feed.entries)} entries"
        return f"❌ {resp.status_code}"
    except Exception as e:
        return f"❌ {e}"

# Test your whitelist
whitelist = yaml.safe_load(Path("data/whitelist_multilingual.yml").read_text()).get("feeds", [])

for feed in whitelist[:10]:  # Test first 10
    print(f"{feed['url']}: {test_feed(feed['url'])}")
