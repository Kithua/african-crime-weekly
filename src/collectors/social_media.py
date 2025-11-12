#!/usr/bin/env python3
import logging
import re
from typing import List, Dict, Any
import requests
import time
from datetime import datetime

log = logging.getLogger(__name__)

KEYWORDS = {
    "terrorism": {"terror", "Jama at Nusrat al-Islam wal Muslimeen", "JNIM", "Islamic State in West Africa", "ISIS-WA", "Islamic State in the Greater Sahara", "ISGS", "Rapid Support Forces", "RSF", "ADF", "M23", "al-shabaab", "boko haram",
                  "isis", "jihad", "attack", "bomb", "suicide", "extremist", "militant", "insurgent"},
    "organised": {"drug", "cocaine", "heroin", "traffick", "smuggl", "mafia", "cartel", "mine illegal", "arms", "weapon", "border", "port", "customs", "kidnap", "ransom", "organized crime"},
    "financial": {"money launder", "bitcoin", "usdt", "fraud", "scam", "ponzi", "pyramid", "ofac", "sanction", "nft", "evasion", "forex", "investment scam", "dnfbp"},
    "cyber": {"ransomware", "phish", "malware", "hack", "breach", "ddos", "botnet", "zero-day", "exploit", "darkweb", "onion", "trojan", "worm", "c&c", "pig butchering", "romance scam"}
}

def _score(text: str) -> str:
    text = text.lower()
    scores = {p: len(kw & set(re.split(r"\W+", text))) for p, kw in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "cyber"

def collect_mastodon(start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    rows = []
    
    mastodon_instances = [
        "https://mastodon.social",
        "https://infosec.exchange",
        "https://ioc.exchange"
    ]
    
    for instance in mastodon_instances:
        try:
            url = f"{instance}/api/v1/timelines/public"
            params = {"limit": 40, "min_id": None}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                toots = response.json()
                
                for toot in toots:
                    toot_time = datetime.fromisoformat(toot["created_at"].replace("Z", "+00:00"))
                    
                    if start_time <= toot_time <= end_time:
                        text = toot.get("content", "")
                        clean_text = re.sub(r'<[^>]+>', '', text)
                        
                        if len(clean_text) > 50:
                            pillar = _score(clean_text)
                            
                            rows.append({
                                "title": clean_text[:100] + "...",
                                "summary": clean_text,
                                "link": toot["url"],
                                "date": toot_time.isoformat(),
                                "source": f"mastodon/{instance}",
                                "tier": "C",
                                "lang": "en",
                                "pillar": pillar,
                                "author": toot["account"]["username"]
                            })
            
            time.sleep(1)
            
        except Exception as e:
            log.warning(f"Mastodon collection failed for {instance}: {e}")
    
    return rows

def collect_reddit(start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    rows = []
    
    subreddits = [
        "cybersecurity", "netsec", "hacking", "osint",
        "AfricanPolitics", "terrorism", "security"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ACW-Bot/1.0)"
    }
    
    for subreddit in subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/new.json"
            params = {"limit": 20}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                posts = response.json()["data"]["children"]
                
                for post in posts:
                    data = post["data"]
                    post_time = datetime.fromtimestamp(data["created_utc"])
                    
                    if start_time <= post_time <= end_time:
                        title = data.get("title", "")
                        text = data.get("selftext", "")
                        combined = title + " " + text
                        
                        if len(combined) > 50:
                            pillar = _score(combined)
                            
                            rows.append({
                                "title": title[:200],
                                "summary": text[:500],
                                "link": f"https://reddit.com{data['permalink']}",
                                "date": post_time.isoformat(),
                                "source": f"reddit/r/{subreddit}",
                                "tier": "C",
                                "lang": "en",
                                "pillar": pillar,
                                "author": data["author"]
                            })
            
            time.sleep(2)
            
        except Exception as e:
            log.warning(f"Reddit collection failed for r/{subreddit}: {e}")
    
    return rows

def collect_all(start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    all_posts = []
    
    try:
        all_posts.extend(collect_mastodon(start_time, end_time))
    except Exception as e:
        log.warning(f"Mastodon collection failed: {e}")
    
    try:
        all_posts.extend(collect_reddit(start_time, end_time))
    except Exception as e:
        log.warning(f"Reddit collection failed: {e}")
    
    log.info(f"Social media collection complete: {len(all_posts)} posts")
    return all_posts
