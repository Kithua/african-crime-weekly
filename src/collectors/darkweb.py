#!/usr/bin/env python3
import logging
import re
from typing import List, Dict, Any
import requests
from datetime import datetime

log = logging.getLogger(__name__)

KEYWORDS = {
    "terrorism": {"terror", "Jama at Nusrat al-Islam wal Muslimeen", "JNIM", "Islamic State in West Africa", "ISIS-WA", "Islamic State in the Greater Sahara", "ISGS", "Rapid Support Forces", "RSF", "ADF", "M23", "al-shabaab", "boko haram",
                  "isis", "jihad", "attack", "bomb", "suicide", "extremist", "militant", "insurgent"},
    "organised": {"drug", "cocaine", "heroin", "traffick", "smuggl", "mafia", "cartel", "mine illegal", "arms", "weapon", "border", "port", "customs", "kidnap", "ransom", "organized crime"},
    "financial": {"money launder", "bitcoin", "usdt", "fraud", "scam", "ponzi", "pyramid", "ofac", "sanction", "nft", "evasion", "forex", "investment scam", "dnfbp", "carding", "smurfing"},
    "cyber": {"ransomware", "phish", "malware", "hack", "breach", "ddos", "botnet", "zero-day", "exploit", "darkweb", "onion", "trojan", "worm", "c&c", "pig butchering", "romance scam"}
}

def _score(text: str) -> str:
    text = text.lower()
    scores = {p: len(kw & set(re.split(r"\W+", text))) for p, kw in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "cyber"

def collect_darkweb_mentions(start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    rows = []
    
    darkweb_monitors = [
        "https://darknetdiaries.com/feed.xml",
        "https://krebsonsecurity.com/feed",
        "https://therecord.media/feed"
    ]
    
    for monitor_url in darkweb_monitors:
        try:
            import feedparser
            
            response = requests.get(monitor_url, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries[:20]:
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        pub_time = datetime(*entry.published_parsed[:6])
                        
                        if start_time <= pub_time <= end_time:
                            text = (entry.title or "") + " " + (entry.summary or "")
                            pillar = _score(text)
                            
                            rows.append({
                                "title": entry.title,
                                "summary": entry.summary,
                                "link": entry.link,
                                "date": pub_time.isoformat(),
                                "source": f"darkweb_monitor/{monitor_url}",
                                "tier": "C",
                                "lang": "en",
                                "pillar": pillar,
                                "classification": "UNCLASSIFIED"
                            })
        
        except Exception as e:
            log.warning(f"Dark web monitor failed {monitor_url}: {e}")
    
    return rows

def collect_cybercrime_forums(start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    rows = []
    
    forum_monitors = [
        {"name": "RaidForums", "url": "https://raids.forums.net", "type": "forum"},
        {"name": "BreachForums", "url": "https://breachforums.st", "type": "forum"},
        {"name": "Nulled", "url": "https://www.nulled.to", "type": "forum"}
    ]
    
    for forum in forum_monitors:
        try:
            response = requests.get(forum["url"], timeout=5)
            if response.status_code == 200:
                log.info(f"Reached {forum['name']} for monitoring reference")
        
        except Exception as e:
            log.debug(f"Forum monitoring reference {forum['name']}: {e}")
    
    return rows

def collect_all(start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    all_intel = []
    
    all_intel.extend(collect_darkweb_mentions(start_time, end_time))
    all_intel.extend(collect_cybercrime_forums(start_time, end_time))
    
    log.info(f"Dark web collection complete: {len(all_intel)} items")
    return all_intel
