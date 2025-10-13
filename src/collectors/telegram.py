"""
Telethon-based public-channel collector.
Only whitelisted channels; no media auto-download.
"""
import os, yaml, datetime as dt, pytz, asyncio, re
from telethon.sessions import StringSession
from telethon import TelegramClient
from pathlib import Path

API_ID   = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION  = os.getenv("TELEGRAM_SESSION_STRING")
WHITELIST = yaml.safe_load(Path("data/whitelist_telegram.yml").read_text())["channels"]

# ----------- helpers -----------
KEYWORDS = {
    "terrorism": {"terror", "al-shabaab", "boko haram", "isis", "jihad", "attack", "bomb", "suicide", "kidnap", "ransom"},
    "organised": {"drug", "cocaine", "heroin", "traffick", "smuggl", "mafia", "cartel", "mine illegal", "arms", "weapon", "border", "port", "customs"},
    "financial": {"money launder", "bitcoin", "usdt", "fraud", "scam", "ponzi", "pyramid", "ofac", "sanction", "vat", "tax evasion", "forex", "investment scam", "business email"},
    "cyber": {"ransomware", "phish", "malware", "hack", "breach", "ddos", "botnet", "zero-day", "exploit", "darkweb", "onion", "c&c", "trojan", "worm", "caffeine", "mrxcoder"}
}

def _score(txt: str) -> str:
    txt = txt.lower()
    scores = {p: len(kw & set(re.split(r"\W+", txt))) for p, kw in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "cyber"

INTEL_MAP = {
    "terrorism": "Channel references regional security; monitor for force-protection indicators.",
    "organised": "Posts discuss smuggling / mining logistics; possible TOC lead.",
    "financial": "Mentions crypto / investment schemes; potential fraud lead.",
    "cyber": "Shares cyber-crime tools / breaches; TTP indicator."
}
# ---------------------------------

async def _fetch_since(start: dt.datetime):
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.connect()
    rows = []
    for ch in WHITELIST:
        try:
            entity = await client.get_entity(ch["username"])
            async for msg in client.iter_messages(entity, offset_date=start, reverse=True):
                if msg.message and msg.date >= start:
                    txt = msg.text or ""
                    pillar = _score(txt)
                    rows.append({
                        "title": txt[:100],
                        "summary": txt,
                        "link": f"https://t.me/{ch['username']}/{msg.id}",
                        "date": msg.date.isoformat(),
                        "source": f"telegram/{ch['username']}",
                        "tier": "B",
                        "lang": "auto",
                        "intel_sentence": INTEL_MAP[pillar]
                    })
        except Exception as e:
            print("Telegram skip", ch, e)
    await client.disconnect()
    return rows

def fetch_since(start: dt.datetime):
    """Synchronous wrapper for GitHub runner."""
    return asyncio.run(_fetch_since(start))
