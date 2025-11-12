#!/usr/bin/env python3
import feedparser
import datetime as dt
import pytz
import os
import yaml
import re
import requests
import logging
from pathlib import Path
from typing import List, Dict, Any

KEYWORDS = {
    "terrorism": {"terror", "Jama at Nusrat al-Islam wal Muslimeen", "JNIM", "Islamic State in West Africa", "ISIS-WA", "Islamic State in the Greater Sahara", "ISGS", "Rapid Support Forces", "RSF", "ADF", "M23", "al-shabaab", "boko haram",
                  "isis", "jihad", "attack", "bomb", "suicide", "extremist", "militant", "insurgent"},
    "organised": {"drug", "cocaine", "heroin", "traffick", "smuggl", "mafia", "cartel", "mine illegal", "arms", "weapon", "border", "port", "customs", "kidnap", "ransom", "organized crime"},
    "financial": {"money launder", "bitcoin", "usdt", "fraud", "scam", "ponzi", "pyramid", "ofac", "sanction", "nft", "evasion", "forex", "investment scam", "dnfbp"},
    "cyber": {"ransomware", "phish", "malware", "hack", "breach", "ddos", "botnet", "zero-day", "exploit", "darkweb", "onion", "trojan", "worm", "c&c", "pig butchering", "romance scam"}
}

INTEL_MAP = {
    "terrorism": "Reports on regional terrorist activities and extremist groups.",
    "organised": "Mentions ports, borders, or mining; potential smuggling or trafficking activity.",
    "financial": "References banking, crypto, or investment schemes; possible fraud lead.",
    "cyber": "Cybersecurity incident or threat reporting."
}

log = logging.getLogger(__name__)

def _score(text: str) -> str:
    text = text.lower()
    scores = {p: len(kw & set(re.split(r"\W+", text))) for p, kw in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "cyber"

def collect(start: dt.datetime, end: dt.datetime) -> List[Dict[str, Any]]:
    rows = []
    whitelist_path = Path("data/whitelist_rss.yml")
    
    if not whitelist_path.exists():
        log.warning(f"Whitelist file not found: {whitelist_path}")
        return rows
    
    whitelist = yaml.safe_load(whitelist_path.read_text()).get("rss", [])
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; ACW-Collector/1.0; +https://github.com/Kithua/african-crime-weekly)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })
    
    for feed_info in whitelist:
        try:
            url = feed_info["url"]
            log.info(f"Fetching RSS: {url}")
            
            resp = session.get(
                url,
                timeout=(10, 30),
                headers={"User-Agent": session.headers["User-Agent"]}
            )
            resp.raise_for_status()
            
            feed = feedparser.parse(resp.text)
            
            if feed.bozo:
                log.warning(f"RSS parse error for {url}: {feed.bozo_exception}")
                continue
            
            for entry in feed.entries:
                try:
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        pub = dt.datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
                    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                        pub = dt.datetime(*entry.updated_parsed[:6], tzinfo=pytz.UTC)
                    else:
                        continue
                    
                    if start <= pub <= end:
                        txt = (entry.title or "") + " " + (entry.summary or "")
                        pillar = _score(txt)
                        
                        rows.append({
                            "title": entry.title,
                            "summary": entry.summary,
                            "link": entry.link,
                            "date": pub.isoformat(),
                            "source": url,
                            "tier": feed_info.get("tier", "B"),
                            "lang": feed_info.get("lang", "en"),
                            "intel_sentence": INTEL_MAP[pillar],
                            "pillar": pillar,
                            "confidence": min(len([kw for kw in KEYWORDS[pillar] if kw in txt.lower()]) / 3, 1.0)
                        })
                except Exception as e:
                    log.warning(f"Error processing entry from {url}: {e}")
                    continue
                    
        except Exception as e:
            log.warning(f"Failed to fetch RSS feed {feed_info.get('url')}: {e}")
            continue
    
    log.info(f"RSS collection complete: {len(rows)} articles")
    return rows
