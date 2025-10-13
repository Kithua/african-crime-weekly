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
    return r.json() if r.ok else None

def _extract_addresses(text):
    pat = re.compile(r'\b(0x[a-fA-F0-9]{40}|bc1[a-z0-9]{39,59}|1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|T[a-zA-Z0-9]{33}|r[a-zA-Z0-9]{24,34})\b')
    return list(set(pat.findall(text)))

# ---------- public collector ----------
def fetch_weekly_africa():
    end   = dt.datetime.utcnow()
    start = end - dt.timedelta(days=7)

    # 1.  dummy payload – replace with real article text next sprint
    dummy_text = """
        0x95222290dd7278aa3ddd389cc1e1d165cc4bafe5 received 12 ETH from 0xBADbadaFF... in Kenya last week.
        bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh sent funds to a Nigerian exchange.
    """
    addresses = _extract_addresses(dummy_text)
    if not addresses:
        return [], {}

    # 2.  query Sentinel ICF v2 /stix
    stix_bundle = _post("/stix", {"pattern": [{"crypto_address": addr} for addr in addresses]})
    if not stix_bundle or stix_bundle.get("status") is False:
        return [], {}

    # 3.  keep only African-tagged objects
    out, iocs = [], {}
    for obj in stix_bundle.get("objects", []):
        labels = obj.get("labels", [])
        african = [l for l in labels if l.upper() in AFRICA_ISO3]
        if african:
            addr = obj.get("x_pattern_value", "unknown")
            country = african[0].title()
            out.append({
                "title": f"Sentinel ICF – {addr}",
                "summary": obj.get("description", "No description"),
                "link": f"https://portal.sentinelprotocol.io/report/{obj.get('id', 'unknown')}",
                "date": obj.get("created", start.isoformat()),
                "source": "sentinel-icf-v2",
                "tier": "A",
                "lang": "en",
                "intel_sentence": f"Crypto-address {addr} flagged for {obj.get('x_security_category', 'suspicious activity')} in {country}."
            })
            # collect real IoCs for template
            if obj.get("x_pattern_subtype") == "ETH":
                iocs["wallet"] = addr
            if refs := obj.get("external_references"):
                for ref in refs:
                    if "ip" in ref.get("url", ""):
                        iocs["ip"] = ref["url"].split("/")[-1]
            if cat := obj.get("x_security_category"):
                iocs["malware"] = cat
            if pat := obj.get("pattern"):
                if "hash" in pat:
                    iocs["hash"] = pat.split("'")[1] if "'" in pat else pat

    return out, iocs
