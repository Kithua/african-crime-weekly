"""
Telethon-based public-channel collector.
Only whitelisted channels; no media auto-download.
"""
import os, yaml, datetime as dt, pytz, asyncio
from telethon.sessions import StringSession
from telethon import TelegramClient
from pathlib import Path

API_ID   = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION  = os.getenv("TELEGRAM_SESSION_STRING")
WHITELIST = yaml.safe_load(open("data/whitelist_telegram.yml"))["channels"]

async def _fetch_since(start: dt.datetime):
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.connect()
    rows = []
    for ch in WHITELIST:
        try:
            entity = await client.get_entity(ch["username"])
            async for msg in client.iter_messages(entity, offset_date=start, reverse=True):
                if msg.message and msg.date >= start:
                    rows.append({
                        "title": msg.message[:100],
                        "summary": msg.message,
                        "link": f"https://t.me/{ch['username']}/{msg.id}",
                        "date": msg.date.isoformat(),
                        "source": f"telegram/{ch['username']}",
                        "tier": "B",
                        "lang": "auto"
                    })
        except Exception as e:
            print("Telegram skip", ch, e)
    await client.disconnect()
    return rows

def fetch_since(start: dt.datetime):
    """Synchronous wrapper for Colab/GitHub Action."""
    return asyncio.run(_fetch_since(start))
