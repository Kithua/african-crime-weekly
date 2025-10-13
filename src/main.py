import os, datetime as dt, pytz, yaml, logging
from src.collectors import rss, telegram, api_sportal, multilingual
from src.nlp import geotag, dedup, classifier
from src.analyst import uk_intel_style
from src.render import pdf, email

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ACW")

def week_range():
    """Return Sunday 00:00 EAT → Saturday 23:59 EAT for last week."""
    today = dt.datetime.now(pytz.timezone("Africa/Nairobi"))
    last_sat = today - dt.timedelta(days=today.weekday()+2)
    sun = last_sat - dt.timedelta(days=6)
    start = sun.replace(hour=0,minute=0,second=0,microsecond=0)
    end   = last_sat.replace(hour=23,minute=59,second=59,microsecond=999999)
    return start, end

def collect(start, end):
    log.info("Collect RSS")
    items = rss.fetch(start, end)
    log.info("Collect Telegram")
    items.extend(telegram.fetch_since(start))
    log.info("Collect Sportal")
    sentinel_items, sentinel_iocs = api_sportal.fetch_weekly_africa()
    items.extend(sentinel_items)
    log.info("Collect multilingual")
    items.extend(multilingual.fetch(start, end))
    return items

def main():
    start, end = week_range()
    items = collect(start, end)
    items = geotag.keep_africa(items)
    items = dedup.remove_duplicates(items)
    buckets = classifier.split_four_pillars(items)
    pdfs = []
    for pillar in buckets:
        report = uk_intel_style.build(buckets[pillar], pillar, start, end,
                                  wallet=sentinel_iocs.get("wallet"),
                                  ip=sentinel_iocs.get("ip"),
                                  malware=sentinel_iocs.get("malware"),
                                  hash=sentinel_iocs.get("hash"))
        outfile = pdf.render(report, pillar, start)
        pdfs.append(outfile)
    email.send(pdfs)          # <-- one call, one e-mail
    log.info("Done")

if __name__ == "__main__":
    main()
