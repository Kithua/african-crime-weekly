import feedparser, datetime as dt, pytz, yaml
def fetch(start, end):
    rows=[]
    wl = yaml.safe_load(open("data/whitelist_multilingual.yml"))["feeds"]
    for w in wl:
        for entry in feedparser.parse(w["url"]).entries:
            pub = dt.datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
            if start <= pub <= end:
                rows.append({"title": entry.title, "summary": entry.summary,
                             "link": entry.link, "date": pub.isoformat(),
                             "source": w["url"], "tier": w["tier"], "lang": w["lang"]})
    return rows
