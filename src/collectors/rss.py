import feedparser, requests, datetime as dt, pytz, os, yaml
from pathlib import Path

WHITELIST = yaml.safe_load(open("data/whitelist_sources.yml")).get("rss",[])

def fetch(start: dt.datetime, end: dt.datetime):
    rows=[]
    for w in WHITELIST:
        try:
            feed = feedparser.parse(w["url"])
            for entry in feed.entries:
                try:
                    pub = dt.datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
                except (AttributeError, TypeError):
                    continue          # skip entries without usable date
                if start <= pub <= end:
                    rows.append({"title": entry.title,
                                 "summary": entry.summary,
                                 "link": entry.link,
                                 "date": pub.isoformat(),
                                 "source": w["url"],
                                 "tier": w.get("tier","B")})
        except Exception as e:
            print("RSS fail", w["url"], e)
    return rows
