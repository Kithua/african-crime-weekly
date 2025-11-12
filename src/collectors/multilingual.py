#!/usr/bin/env python3
import feedparser
import logging
import re
import requests
import yaml
from pathlib import Path
import datetime as dt
import pytz
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import List, Dict, Any

KEYWORDS = {
    "terrorism": {"terror", "Jama at Nusrat al-Islam wal Muslimeen", "JNIM", "Islamic State in West Africa", "ISIS-WA", "Islamic State in the Greater Sahara", "ISGS", "Rapid Support Forces", "RSF", "ADF", "M23", "al-shabaab", "boko haram",
                  "isis", "jihad", "attack", "bomb", "suicide", "extremist", "militant", "insurgent"},
    "organised": {"drug", "cocaine", "heroin", "traffick", "smuggl", "mafia", "cartel", "mine illegal", "arms", "weapon", "border", "port", "customs", "kidnap", "ransom", "organized crime"},
    "financial": {"money launder", "bitcoin", "usdt", "fraud", "scam", "ponzi", "pyramid", "ofac", "sanction", "nft", "evasion", "forex", "investment scam", "dnfbp"},
    "cyber": {"ransomware", "phish", "malware", "hack", "breach", "ddos", "botnet", "zero-day", "exploit", "darkweb", "onion", "trojan", "worm", "c&c", "pig butchering", "romance scam"}
}

INTEL_MAP = {
    "terrorism": "Regional conflict reporting; follow for local sentiment.",
    "organised": "Mentions ports / borders; potential smuggling angle.",
    "financial": "Banking / crypto references; fraud or laundering lead.",
    "cyber": "No cyber keywords – default bucket."
}

log = logging.getLogger(__name__)

def get_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504, 403],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; ACW-Bot/1.0; +https://github.com/Kithua/african-crime-weekly)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return session

session = get_session()

def _score(text: str) -> str:
    text = text.lower()
    scores = {p: len(kw & set(re.split(r"\W+", text))) for p, kw in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "cyber"

def collect(start: dt.datetime, end: dt.datetime) -> List[Dict[str, Any]]:
    rows = []
    whitelist_path = Path("data/whitelist_multilingual.yml")
    
    if not whitelist_path.exists():
        log.warning(f"Whitelist file not found: {whitelist_path}")
        return rows
    
    whitelist = yaml.safe_load(whitelist_path.read_text()).get("feeds", [])
    
    for feed_info in whitelist:
        try:
            url = feed_info["url"]
            log.info(f"Fetching multilingual RSS: {url}")
            
            resp = session.get(
                url,
                timeout=(10, 30),
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
                        text = (entry.title or "") + " " + (entry.summary or "")
                        pillar = _score(text)
                        
                        rows.append({
                            "title": entry.title,
                            "summary": entry.summary,
                            "link": entry.link,
                            "date": pub.isoformat(),
                            "source": url,
                            "tier": feed_info.get("tier", "B"),
                            "lang": feed_info.get("lang", "en"),
                            "intel_sentence": INTEL_MAP[pillar],
                            "pillar": pillar
                        })
                except Exception as e:
                    log.warning(f"Error processing multilingual entry: {e}")
                    continue
                    
        except Exception as e:
            log.warning(f"Failed to fetch feed {feed_info.get('url')}: {e}")
            continue
    
    log.info(f"Multilingual collection complete: {len(rows)} articles")
    return rows
