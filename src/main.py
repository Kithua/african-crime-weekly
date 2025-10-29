import os, datetime as dt, pytz, yaml, logging
from pathlib import Path
from src.collectors import rss, telegram, api_sportal, multilingual
from src.nlp import geotag, dedup, classifier
from src.analyst import uk_intel_style
from src.render import pdf, email

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ACW")


def week_range():
    today = dt.datetime.now(pytz.timezone("Africa/Nairobi"))
    last_sat = today - dt.timedelta(days=today.weekday() + 2)
    sun = last_sat - dt.timedelta(days=6)
    start = sun.replace(hour=0, minute=0, second=0, microsecond=0)
    end = last_sat.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def collect(start, end):
    log.info("Collect RSS")
    items = rss.fetch(start, end)
    log.info("Collect Telegram")
    items.extend(telegram.fetch_since(start))
    log.info("Collect Sentinel ICF")
    sentinel_items, sentinel_iocs = api_sportal.fetch_weekly_africa()
    items.extend(sentinel_items)
    log.info("Collect multilingual")
    items.extend(multilingual.fetch(start, end))
    return items, sentinel_iocs


def main():
    start, end = week_range()
    items, sentinel_iocs = collect(start, end)

    items = geotag.keep_africa(items)
    items = dedup.remove_duplicates(items)
    buckets = classifier.split_four_pillars(items)

    report = uk_intel_style.build(
        buckets["terrorism"], buckets["organised"], buckets["financial"], buckets["cyber"],
        start, end
    )
    # pass real IoCs only to cyber section
    report = report.replace("{{ wallet }}", str(sentinel_iocs.get("wallet")))
    report = report.replace("{{ ip }}", str(sentinel_iocs.get("ip")))
    report = report.replace("{{ malware }}", str(sentinel_iocs.get("malware")))
    report = report.replace("{{ hash }}", str(sentinel_iocs.get("hash")))

    week_str = start.strftime('%Y-W%U')
    outfile = Path(f"{week_str}-African-Crime-Weekly.pdf")
    from weasyprint import HTML
    HTML(string=report).write_pdf(outfile)

    email.send([outfile])   # one e-mail, one PDF
    log.info("Done")


if __name__ == "__main__":
    main()
