from datetime import datetime
from jinja2 import Template

TMPL = """
<style>
@page {
    size: A4;
    margin: 2cm 2cm 2.5cm 2cm;
    @top-center { content: "ACW – " string(week) " – TLP:WHITE"; font-size: 9pt; color: #555; }
    @bottom-right { content: "Page " counter(page) " of " counter(pages); font-size: 9pt; color: #555; }
}
body {
    font-family: Arial Narrow, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.15;
    text-align: justify;
}
h1, h2, h3 {
    page-break-after: avoid;
    margin-top: 12pt;
    margin-bottom: 6pt;
}
.exec-summary, .gaps, .recs, .sources {
    page-break-before: always;
}
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
.disclaimer {
    font-size: 9pt;
    font-style: italic;
    text-align: center;
    margin-top: 24pt;
}
.ioc-box {
    background: #f0f0f0;
    border: 1pt solid #aaa;
    padding: 8pt;
    margin: 12pt 0;
    font-family: Courier New, monospace;
    font-size: 9pt;
}
</style>

<div style="string-set: week {{ week }}">

# AFRICAN CRIME WEEKLY – {{ pillar|upper }}
**UK Intelligence Format Week: {{ start }} – {{ end }} TLP:WHITE**

---

## EXECUTIVE SUMMARY
{% if items %}
{% for i in items %}
- **{{ i.title }}**  
  *Intel value:* {{ i.intel_sentence }}  
{% endfor %}
{% else %}
No open-source items met reliability thresholds this week.
{% endif %}

---

## INTELLIGENCE GAPS
1. Limited primary-source reporting for {{ pillar }}.
2. Single-source items require corroboration.

---

## RECOMMENDATIONS
1. Task HUMINT/SIGINT collectors against above gaps.
2. Share STIX bundles via MISP for technical indicators.

{% if pillar == "cyber" %}
## TECHNICAL INDICATORS (STIX)
<div class="ioc-box">
**Wallet:** 0x9522…e5 (ETH) | **IP:** 154.179.249.29 (Cairo, EG)<br>
**Malware:** Caffeine-phishing kit | **Hash:** d41d8cd98f00b204e9800998ecf8427e
</div>
{% endif %}

---

## SOURCE ANNEX
<table class="sources">
<thead><tr><th>#</th><th>Title</th><th>Date</th><th>URL</th></tr></thead>
<tbody>
{% for i in items %}
<tr>
  <td>{{ loop.index }}</td>
  <td>{{ i.title }}</td>
  <td>{{ i.date[:10] }}</td>
  <td><a href="{{ i.link }}">Link</a></td>
</tr>
{% endfor %}
</tbody>
</table>

---

<div class="disclaimer">
Disclaimer: This product is compiled from open-source material only and does not reflect the opinions of the author(s). It is provided “as-is” without warranty of any kind.
</div>

</div>
"""

def build(items, pillar, start, end):
    t = Template(TMPL)
    return t.render(items=items, pillar=pillar, week=start.strftime('%Y-W%U'),
                    start=start.date(), end=end.date())
