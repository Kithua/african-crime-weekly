"""
Sentinel Portal (Sportal) – African crypto-crime reports.
"""
import os, requests, datetime as dt

API_KEY = os.getenv("SENTINEL_API_KEY")
BASE    = "https://portal.sentinelprotocol.io/api/v1"

AFRICA_ISO3 = {"DZA","AGO","BEN","BWA","BFA","BDI","CMR","CPV","CAF","TCD","COM","COG","COD","CIV","DJI","EGY","GNQ","ERI","SWZ","ETH","GAB","GMB","GHA","GIN","GNB","KEN","LSO","LBR","LBY","MDG","MWI","MLI","MRT","MUS","MAR","MOZ","NAM","NER","NGA","RWA","STP","SEN","SYC","SLE","SOM","ZAF","SSD","SDN","TZA","TGO","TUN","UGA","ZMB","ZWE"}

def fetch_weekly_africa():
    end   = dt.datetime.utcnow()
    start = end - dt.timedelta(days=7)
    params = {
        "api_key": API_KEY,
        "tags": "africa,terrorism,scam,pig-butchering",
        "from": start.isoformat(),
        "to": end.isoformat(),
        "size": 200
    }
    r = requests.get(f"{BASE}/reports", params=params, timeout=60)
    r.raise_for_status()
    hits = [h for h in r.json()["hits"] if any(c in AFRICA_ISO3 for c in h.get("countries", []))]
    out = []
    for h in hits:
        out.append({
            "title": h.get("title", "No title"),
            "summary": h.get("description", ""),
            "link": f"https://portal.sentinelprotocol.io/report/{h['id']}",
            "date": h.get("published", start.isoformat()),
            "source": "sentinel-portal",
            "tier": "A",
            "lang": "en"
        })
    return out
