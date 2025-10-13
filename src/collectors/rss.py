import feedparser, datetime as dt, pytz, os, yaml, re
from pathlib import Path

# pillar keywords
KEYWORDS = {
    "terrorism": {"terror", "al-shabaab", "boko haram", "isis", "jihad", "attack", "bomb", "suicide", "kidnap", "ransom"},
    "organised": {"drug", "cocaine", "heroin", "traffick", "smuggl", "mafia", "cartel", "mine illegal", "arms", "weapon", "border", "port", "customs"},
    "financial": {"money launder", "bitcoin", "usdt", "fraud", "scam", "ponzi", "pyramid", "ofac", "sanction", "vat", "tax evasion", "forex", "investment scam", "business email"},
    "cyber": {"ransomware", "phish", "malware", "hack", "breach", "ddos", "botnet", "zero-day", "exploit", "darkweb", "onion", "c&c", "trojan", "worm", "caffeine", "mrxcoder"}
}

# truth-map for RSS items
INTEL_MAP = {
    "terrorism": "Reports on AUSSOM / al-Shabaam activity; potential force-protection intel for KE contingent.",
    "organised": "Mentions port / mining / border activity; watch for smuggling or illicit mineral flows.",
    "financial": "References investment / crypto / banking; possible scam or laundering lead.",
    "cyber": "No cyber keywords detected – default bucket."
}

def _score(txt: str) -> str:
    txt = txt.lower()
    scores = {p: len(kw & set(re.split(r"\W+", txt))) for p, kw in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "cyber"

def fetch(start: dt.datetime, end: dt.datetime):
    rows = []
    whitelist = yaml.safe_load(Path("data/whitelist_sources.yml").read_text()).get("rss", [])
    for w in whitelist:
        try:
            feed = feedparser.parse(w["url"])
            for entry in feed.entries:
                try:
                    pub = dt.datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
                except (AttributeError, TypeError):
                    continue
                if start <= pub <= end:
                    txt = entry.title + " " + entry.summary
                    pillar = _score(txt)
                    rows.append({
                        "title": entry.title,
                        "summary": entry.summary,
                        "link": entry.link,
                        "date": pub.isoformat(),
                        "source": w["url"],
                        "tier": w.get("tier", "B"),
                        "lang": "en",
                        "intel_sentence": INTEL_MAP[pillar]
                    })
        except Exception as e:
            print("RSS fail", w["url"], e)
    return rows
