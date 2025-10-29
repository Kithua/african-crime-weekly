"""
Collate the last 6 full days (Mon-Sat when run on Sun),
run the existing NLP pipeline, and write
data/weekly/YYYY-Www.json  for the render step.
"""
import os, json, glob, datetime, pandas as pd
from src.nlp import classifier, dedup, geotag, translate
from src.collectors import rss, telegram, api_sportal   # re-use existing collectors

WEEKLY_DIR = "data/weekly"
os.makedirs(WEEKLY_DIR, exist_ok=True)

def daterange():
    """Return list of YYYY-MM-DD for last 6 full days."""
    today = datetime.datetime.utcnow().date()
    return [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1,7)]

def load_articles(days):
    articles = []
    for d in days:
        path = f"data/raw/{d}.jsonl"
        if os.path.exists(path):
            with open(path) as f:
                articles.extend([json.loads(l) for l in f])
    return articles

def main():
    days   = daterange()
    iso_week = datetime.datetime.utcnow().strftime("%G-W%V")
    articles = load_articles(days)

    # existing pipeline – exactly what main.py does daily
    articles = dedup.remove_duplicates(articles)
    for art in articles:
        art["crime_tags"]   = classifier.predict(art["body_en"])
        art["geo"]          = geotag.extract(art)
        art["confidence"]   = classifier.confidence(art)

    # split by crime pillar for template
    pillars = {
        "terrorism":   [a for a in articles if "terrorism"   in a["crime_tags"]],
        "organised":   [a for a in articles if "organised"   in a["crime_tags"]],
        "financial":   [a for a in articles if "financial"   in a["crime_tags"]],
        "cyber":       [a for a in articles if "cyber"       in a["crime_tags"]],
    }

    weekly = {
        "iso_week": iso_week,
        "days": days,
        "articles": articles,
        "pillars":  {k: len(v) for k, v in pillars.items()},
        "top5":     sorted(articles, key=lambda x: x["confidence"], reverse=True)[:5],
        "matrix":   build_matrix(articles)   # 4×4 credibility grid
    }

    out = f"{WEEKLY_DIR}/{iso_week}.json"
    with open(out, "w", encoding="utf8") as f:
        json.dump(weekly, f, ensure_ascii=False, indent=2)
    print("Weekly bundle →", out)

def build_matrix(articles):
    """Return 4×4 dict for template."""
    # A=official, B=vetted-media, C=NGO, D=anon
    # 1=confirmed, 2=probable, 3=possible, 4=doubtful
    matrix = {g: {c: 0 for c in range(1,5)} for g in "ABCD"}
    for art in articles:
        g = art.get("source_grade", "C")   # default NGO if not graded
        c = art.get("confirmation", 3)     # default possible
        matrix[g][c] += 1
    return matrix

if __name__ == "__main__":
    main()
