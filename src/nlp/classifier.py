"""
Zero-shot classifier stub.
Returns hard-coded buckets until real impl. added.
"""
def split_four_pillars(items):
    buckets = {"terrorism": [], "organised": [], "financial": [], "cyber": []}
    for it in items:
        text = (it.get("title","")+" "+it.get("summary","")).lower()
        if any(k in text for k in ("terror","extrem","boko haram","al-shabaab","jihad","isis")):
            buckets["terrorism"].append(it)
        elif any(k in text for k in ("drug","traffick","cocaine","heroin","smuggl","mafia","cartel")):
            buckets["organised"].append(it)
        elif any(k in text for k in ("money launder","bitcoin","scam","fraud","sanctions","ofac")):
            buckets["financial"].append(it)
        elif any(k in text for k in ("cyber","hack","ransom","phish","malware")):
            buckets["cyber"].append(it)
        else:
            buckets["cyber"].append(it)   # default bucket for now
    return buckets
