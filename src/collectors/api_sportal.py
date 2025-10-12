"""
Sentinel Protocol ICF v2  (STIX format)
- queries addresses found in the week’s OSINT
- returns STIX objects per African country
"""
import os, requests, datetime as dt, re
from pathlib import Path

BASE    = "https://icf.api.sentinelprotocol.io/v2"
API_KEY = os.getenv("SENTINEL_API_KEY")
AFRICA_ISO3 = {"DZA","AGO","BEN","BWA","BFA","BDI","CMR","CPV","CAF","TCD","COM","COG","COD","CIV","DJI","EGY","GNQ","ERI","SWZ","ETH","GAB","GMB","GHA","GIN","GNB","KEN","LSO","LBR","LBY","MDG","MWI","MLI","MRT","MUS","MAR","MOZ","NAM","NER","NGA","RWA","STP","SEN","SYC","SLE","SOM","ZAF","SSD","SDN","TZA","TGO","TUN","UGA","ZMB","ZWE"}

# ---------- helpers ----------
def _post(path, payload):
    r = requests.post(f"{BASE}{path}", json=payload, headers={"x-api-key": API_KEY}, timeout=30)
    if not r.ok:                       # 4xx/5xx → no data
        return None
    return r.json()                    # STIX JSON or None

def _extract_addresses(text):
    """Very simple BTC / ETH / BNB / TRX / XRP grabber."""
    pat = re.compile(r'\b(0x[a-fA-F0-9]{40}|bc1[a-z0-9]{39,59}|1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|T[a-zA-Z0-9]{33}|r[a-zA-Z0-9]{24,34})\b')  # ETH, BTC, TRX, XRP
    return list(set(pat.findall(text)))

# ---------- public collector ----------
def fetch_weekly_africa():
    end   = dt.datetime.utcnow()
    start = end - dt.timedelta(days=7)
    # 1.  dummy payload – in real life you feed the week’s articles here
    dummy_text = """
        0x95222290dd7278aa3ddd389cc1e1d165cc4bafe5 received 12 ETH from 0xBADbadaFF... in Kenya last week.
        bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh sent funds to a Nigerian exchange.
    """
    addresses = _extract_addresses(dummy_text)        # TODO: feed real articles
    if not addresses:
        return []

    # 2.  query Sentinel ICF v2 /stix  (gives full STIX bundle)
    stix_bundle = _post("/stix", {"pattern": [{"crypto_address": addr} for addr in addresses]})
    if not stix_bundle or stix_bundle.get("status") is False:
        return []

    # 3.  keep only objects that mention an African country
    out = []
    for obj in stix_bundle.get("objects", []):
        labels = obj.get("labels", [])
        # Sentinel puts country tag in labels  e.g.  ["kenya","financial-crime"]
        african = [l for l in labels if l.upper() in AFRICA_ISO3]
        if african:
            out.append({
                "title": f"Sentinel ICF – {obj['x_pattern_value']}",
                "summary": obj.get("description", "No description"),
                "link": obj.get("external_references", [{}])[0].get("url", "https://portal.sentinelprotocol.io"),
                "date": obj.get("created", start.isoformat()),
                "source": "sentinel-icf-v2",
                "tier": "A",
                "lang": "en",
                "stix_object": obj
            })
    return out
