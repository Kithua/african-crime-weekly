import re

# pillar-specific keywords
KEYWORDS = {
    "terrorism": {"terror", "al-shabaab", "boko haram", "isis", "jihad", "extrem", "attack", "bomb", "suicide", "kidnap", "ransom"},
    "organised": {"drug", "cocaine", "heroin", "traffick", "smuggl", "mafia", "cartel", "mine illegal", "arms", "weapon", "border", "port", "customs"},
    "financial": {"money launder", "bitcoin", "usdt", "fraud", "scam", "ponzi", "pyramid", "ofac", "sanction", "vat", "tax evasion", "forex", "investment scam", "business email"},
    "cyber": {"ransomware", "phish", "malware", "hack", "breach", "ddos", "botnet", "zero-day", "exploit", "darkweb", "onion", "c&c", "trojan", "worm", "caffeine", "mrxcoder"}
}

def split_four_pillars(items):
    buckets = {p: [] for p in KEYWORDS}
    for it in items:
        txt = (it.get("title", "") + " " + it.get("summary", "")).lower()
        scores = {p: len(kw & set(re.split(r"\W+", txt))) for p, kw in KEYWORDS.items()}
        best = max(scores, key=scores.get) if max(scores.values()) else "cyber"
        buckets[best].append(it)
    return buckets
