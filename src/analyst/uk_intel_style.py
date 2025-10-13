from datetime import datetime
from jinja2 import Template

TMPL = """
AFRICAN CRIME WEEKLY – {{ pillar|upper }}
(UK Intelligence Format)

Week: {{ start }} to {{ end }}
Executive Summary
=================
{% if items %}
  {% for i in items %}
- {{ i.title }} ({{ i.source }})
  {% endfor %}
{% else %}
No open-source items met reliability thresholds this week.
{% endif %}

Intelligence Gaps
=================
1. Limited primary-source reporting for {{ pillar }}.
2. Single-source items require corroboration.

Recommendations
===============
1. Task HUMINT / SIGINT collectors against above gaps.
2. Share STIX bundles via MISP for technical indicators.

Source Annex
============
{% for i in items %}
{{ loop.index }}. {{ i.title }} – {{ i.link }} (Reliability: {{ i.tier }})
{% endfor %}

Disclaimer: This product is compiled from open-source material only
and does not reflect the opinions of the author(s).
"""

def build(items, pillar, start, end):
    t = Template(TMPL)
    return t.render(items=items, pillar=pillar, start=start.date(), end=end.date())
