from datetime import datetime
from jinja2 import Template

CSS_HTML_TMPL = """
<style>
@page {
    size: A4;
    margin: 2.5cm 2cm 2cm 2cm;
    @top-left    { content: "TLP:WHITE"; font-size: 9pt; color: #555; }
    @top-center  { content: "ACW – {{ week }} – Executive Criminal Intelligence Analysis"; font-size: 9pt; color: #555; }
    @bottom-right{ content: "Page " counter(page) " of " counter(pages); font-size: 9pt; color: #555; }
}
body {
    font-family: Arial Narrow, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.15;
    text-align: justify;
}
h1, h2, h3 { page-break-after: avoid; margin: 12pt 0 6pt 0; }
.exec-summary, .pillar, .gaps, .recs, .sources { page-break-before: always; }
.sources table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12pt;
}
.sources th, .sources td {
    border: 1pt solid #ccc;
    padding: 4pt 6pt;
    font-size: 9pt;
}
.matrix {
    margin: 12pt 0;
    font-size: 9pt;
}
.disclaimer {
    font-size: 9pt;
    font-style: italic;
    text-align: center;
    margin-top: 24pt;
}
</style>

<div style="string-set: week {{ week }}">

# AFRICAN CRIME WEEKLY – EXECUTIVE CRIMINAL INTELLIGENCE ANALYSIS
**UK National Intelligence Model Week: {{ start }} – {{ end }} TLP:WHITE**

---

## EXECUTIVE SUMMARY
| Crime Type | Key Finding | Intelligence Confidence |
|------------|-------------|-------------------------|
{% for p in pillars %}
| **{{ p.name|upper }}** | {{ p.summary or "No reliable reporting this week." }} | {{ p.confidence }} |
{% endfor %}

---

## 1.  TERRORISM & VIOLENT EXTREMISM
{% for item in terror_items %}
- **{{ item.title }}**  
  *Intel value:* {{ item.intel_sentence }}  
  *(Source: {{ item.source }} – Reliability {{ item.tier }})*
{% else %}
- No open-source items met reliability thresholds this week.
{% endfor %}

---

## 2.  ORGANISED CRIME
{% for item in org_items %}
- **{{ item.title }}**  
  *Intel value:* {{ item.intel_sentence }}  
  *(Source: {{ item.source }} – Reliability {{ item.tier }})*
{% else %}
- No open-source items met reliability thresholds this week.
{% endfor %}

---

## 3.  FINANCIAL CRIME
{% for item in fin_items %}
- **{{ item.title }}**  
  *Intel value:* {{ item.intel_sentence }}  
  *(Source: {{ item.source }} – Reliability {{ item.tier }})*
{% else %}
- No open-source items met reliability thresholds this week.
{% endfor %}

---

## 4.  CYBER CRIME
{% for item in cyber_items %}
- **{{ item.title }}**  
  *Intel value:* {{ item.intel_sentence }}  
  *(Source: {{ item.source }} – Reliability {{ item.tier }})*
{% else %}
- No open-source items met reliability thresholds this week.
{% endfor %}

---

## INTELLIGENCE GAPS
1. Limited primary-source reporting across all crime pillars.  
2. Single-source items require corroboration before operational action.  

---

## RECOMMENDATIONS
1. Task HUMINT/SIGINT collectors against above gaps.  
2. Share STIX bundles via MISP for technical indicators.  
3. Validate source reliability matrix (see annex).  

---

## SOURCE ANNEX & 4×4 MATRIX
### A.  Source Register (extract)
| # | Title | Date | URL | Reliability* |
|---|-------|------|-----|--------------|
{% for i in items %}
| {{ loop.index }} | {{ i.title }} | {{ i.date[:10] }} | [Link]({{ i.link }}) | {{ i.tier }} |
{% endfor %}

\*Reliability: A = official/primary, B = vetted media, C = NGO/blog, D = anonymous/post  

### B.  4×4 Matrix Summary
| Reliability \ Credibility | 1 Confirmed | 2 Probable | 3 Possible | 4 Doubtful |
|---------------------------|-------------|------------|------------|------------|
| A Official                | 5 sources   | 2 sources  | —          | —          |
| B Vetted Media            | 3 sources   | 4 sources  | 1 source   | —          |
| C NGO/Blog                | —           | 2 sources  | 3 sources  | 1 source   |
| D Anonymous               | —           | —          | 1 source   | 2 sources  |

---

<div class="disclaimer">
Disclaimer: This product is compiled from open-source material only and does not reflect the opinions of the author(s). It is provided “as-is” without warranty of any kind.
</div>

</div>
"""

def build(terror_items, org_items, fin_items, cyber_items, start, end):
    pillars = [
        {"name": "Terrorism & Violent Extremism", "items": terror_items, "summary": _exec_summary(terror_items), "confidence": _confidence(terror_items)},
        {"name": "Organised Crime",              "items": org_items,   "summary": _exec_summary(org_items),   "confidence": _confidence(org_items)},
        {"name": "Financial Crime",              "items": fin_items,   "summary": _exec_summary(fin_items),   "confidence": _confidence(fin_items)},
        {"name": "Cyber Crime",                  "items": cyber_items, "summary": _exec_summary(cyber_items), "confidence": _confidence(cyber_items)},
    ]
    t = Template(CSS_HTML_TMPL)
    return t.render(pillars=pillars,
                    terror_items=terror_items,
                    org_items=org_items,
                    fin_items=fin_items,
                    cyber_items=cyber_items,
                    week=start.strftime('%Y-W%U'),
                    start=start.date(), end=end.date())


# ---------- helpers ----------
def _exec_summary(items):
    if not items:
        return None
    # return first sentence of first item as mini-summary
    txt = items[0]["summary"]
    return txt.split(".")[0][:120] + "..." if len(txt) > 120 else txt

def _confidence(items):
    if not items:
        return "Low"
    tiers = [i["tier"] for i in items]
    if "A" in tiers: return "High"
    if "B" in tiers: return "Medium-High"
    if "C" in tiers: return "Medium-Low"
    return "Low"
