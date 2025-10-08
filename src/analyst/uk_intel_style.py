from jinja2 import Template
import datetime as dt, yaml, os

TMPL = """
African Crime Weekly – {{ pillar }}
Week: {{ start }} to {{ end }}
Items: {{ items|length }}
{% for i in items %}
- {{ i.title }} ({{ i.source }})
{% endfor %}
"""

def build(items, pillar, start, end):
    t = Template(TMPL)
    return t.render(items=items, pillar=pillar, start=start.date(), end=end.date())
