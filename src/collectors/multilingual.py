import feedparser, datetime as dt, pytz, yaml, re
from pathlib import Path

# pillar keywords (same as RSS / Telegram)
KEYWORDS = {
    "terrorism": {"terror", "al-shabaab", "boko haram", "isis", "jihad", "attack", "bomb", "suicide", "kidnap", "ransom"},
    "organised": {"drug", "cocaine", "heroin", "traffick", "smuggl", "mafia", "cartel", "mine illegal", "arms", "weapon", "border", "port", "customs"},
    "financial": {"money launder", "bitcoin", "usdt", "fraud", "scam", "ponzi", "pyramid", "ofac", "sanction", "vat", "tax evasion", "forex", "investment scam", "business email"},
    "cyber": {"ransomware", "phish", "malware", "hack", "breach", "ddos", "botnet", "zero-day", "exploit", "darkweb", "onion", "c&c", "trojan", "worm", "BEC", "threat actor"}
}

def _score(txt: str) -> str:
    txt = txt.lower()
    scores = {p: len(kw & set(re.split(r"\W+", txt))) for p, kw in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "cyber"

INTEL_MAP = {
    "terrorism": "Non-English reporting on regional conflict; follow for local sentiment.",
    "organised": "References cross-border trade / ports; possible smuggling angle.",
    "financial": "Covers banking / crypto stories; fraud or laundering angle.",
    "cyber": "No cyber keywords – default bucket."
}

def fetch(start: dt.datetime, end: dt.datetime):
    rows = []
    wl = yaml.safe_load(Path("data/whitelist_multilingual.yml").read_text()).get("feeds", [])
    for w in wl:
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
                    "tier": w["tier"],
                    "lang": w["lang"],
                    "intel_sentence": INTEL_MAP[pillar]
                })
    return rows
