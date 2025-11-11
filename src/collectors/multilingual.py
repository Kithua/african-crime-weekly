import feedparser, datetime as dt, pytz, yaml, re
import logging, requests   # add at top
from pathlib import Path



# pillar keywords (same as RSS / Telegram)
KEYWORDS = {
    "terrorism": {"terror", "al-shabaab", "boko haram", "isis", "jihad", "attack", "bomb", "suicide", "kidnap", "ransom"},
    "organised": {"drug", "cocaine", "heroin", "traffick", "smuggl", "mafia", "cartel", "mine illegal", "arms", "weapon", "border", "port", "customs"},
    "financial": {"money launder", "bitcoin", "usdt", "fraud", "scam", "ponzi", "pyramid", "ofac", "sanction", "vat", "tax evasion", "forex", "investment scam", "business email"},
    "cyber": {"ransomware", "phish", "malware", "hack", "breach", "ddos", "botnet", "zero-day", "exploit", "darkweb", "onion", "c&c", "trojan", "worm", "BEC", "threat actor"}
}


INTEL_MAP = {
    "terrorism": "Non-English reporting on regional conflict; follow for local sentiment.",
    "organised": "References cross-border trade / ports; possible smuggling angle.",
    "financial": "Covers banking / crypto stories; fraud or laundering angle.",
    "cyber": "No cyber keywords – default bucket."
}

log = logging.getLogger(__name__)

def _score(txt: str) -> str:
    txt = txt.lower()
    scores = {p: len(kw & set(re.split(r"\W+", txt))) for p, kw in KEYWORDS.items()}
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
                headers={"User-Agent": "ACW/1.0 (+https://github.com/Kithua/african-crime-weekly)"},
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
