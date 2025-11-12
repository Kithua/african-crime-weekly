"""
Multilingual RSS collector
- skips dead feeds instead of crashing
"""
import feedparser
import logging
import re
import requests
import yaml
from pathlib import Path
import datetime as dt
import pytz

# same keywords you already use
KEYWORDS = {
    "terrorism": {"terror", "al-shabaab", "boko haram", "isis", "jihad", "attack", "bomb", "suicide", "kidnap", "ransom"},
    "organised": {"drug", "cocaine", "heroin", "traffick", "smuggl", "mafia", "cartel", "mine illegal", "arms",
                  "weapon", "border", "port", "customs"},
    "financial": {"money launder", "bitcoin", "usdt", "fraud", "scam", "ponzi", "pyramid", "ofac", "sanction",
                  "vat", "evasion", "forex", "investment scam", "business email"},
    "cyber": {"ransomware", "phish", "malware", "hack", "breach", "ddos", "botnet", "zero-day", "exploit",
              "darkweb", "onion", "trojan", "worm", "c&c", "caffeine", "mrxcoder"}
}

INTEL_MAP = {
    "terrorism": "Regional conflict reporting; follow for local sentiment.",
    "organised": "Mentions ports / borders; potential smuggling angle.",
    "financial": "Banking / crypto references; fraud or laundering lead.",
    "cyber": "No cyber keywords – default bucket."
}

log = logging.getLogger(__name__)

def _score(text: str) -> str:
    text = text.lower()
    scores = {p: len(kw & set(re.split(r"\W+", text))) for p, kw in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "cyber"

def fetch(start: dt.datetime, end: dt.datetime):
    rows = []
    whitelist = yaml.safe_load(Path("data/whitelist_multilingual.yml").read_text()).get("feeds", [])

    for feed_info in whitelist:
        try:
            # fetch with short timeout + custom UA
            resp = requests.get(
                feed_info["url"],
                timeout=(5, 10),
                headers=headers={
                                    "User-Agent": "Mozilla/5.0 (compatible; ACW-Bot/1.0; +https://github.com/Kithua/african-crime-weekly)",
                                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                    "Accept-Language": "en-US,en;q=0.5",
                                    "Accept-Encoding": "gzip, deflate",
                                    "DNT": "1",
                                    "Connection": "keep-alive",
                                    "Upgrade-Insecure-Requests": "1",
                                },
            )
            resp.raise_for_status()

            # parse only if we got text
            feed = feedparser.parse(resp.text)

        except Exception as exc:
            log.warning("Bad feed %s : %s", feed_info["url"], exc)
            continue   # <-- skip this feed, keep going

        # existing extraction logic
        for entry in feed.entries:
            try:
                pub = dt.datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
            except (AttributeError, TypeError):
                continue
            if start <= pub <= end:
                text = (entry.title or "") + " " + (entry.summary or "")
                pillar = _score(text)
                rows.append({
                    "title": entry.title,
                    "summary": entry.summary,
                    "url": entry.link,
                    "date": pub.isoformat(),
                    "source": feed_info["url"],
                    "tier": feed_info.get("tier", "B"),
                    "lang": feed_info["lang"],
                    "intel_sentence": INTEL_MAP[pillar],
                })

    return rows
