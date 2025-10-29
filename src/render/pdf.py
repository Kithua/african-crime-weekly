from weasyprint import HTML, CSS
from pathlib import Path
import datetime as dt

# --- A4 UK-Intel house style -----------------------------------------------
A4_CSS = """
@page {
    size: A4;
    margin: 2cm 2cm 2.5cm 2cm;          /* top right bottom left */
    @top-center { content: "ACW – " string(week) " – TLP:WHITE"; font-size: 9pt; color: #555; }
    @bottom-right { content: "Page " counter(page) " of " counter(pages); font-size: 9pt; color: #555; }
}

body {
    font-family: Arial Narrow, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.15;
    text-align: justify;
}

h1, h2, h3 { page-break-after: avoid; margin-top: 12pt; margin-bottom: 6pt; }
.exec-summary, .gaps, .recs, .sources { page-break-before: always; }

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
"""

# ---------------------------------------------------------------------------
def render(html: str, pillar: str, start: dt.datetime) -> Path:
    week_str = start.strftime('%Y-W%U')
    outfile = Path(f"{week_str}-{pillar}.pdf")

    # Inject the week string into the HTML so the running header can read it
    html = f'<style>{A4_CSS}</style><div style="string-set: week {week_str}">{html}</div>'

    HTML(string=html).write_pdf(outfile, stylesheets=[CSS(string=A4_CSS)])
    # inside pdf.py  –  add alternative entry point
    if sys.argv[1] == "weekly":
        iso_week = datetime.datetime.utcnow().strftime("%G-W%V")
        with open(f"data/weekly/{iso_week}.json") as f:
            bundle = json.load(f)
        html = populate_template("templates/weekly_template.html", bundle)
        pdf_path = f"data/weekly/{iso_week}.pdf"
        weasyprint.HTML(string=html).write_pdf(pdf_path)
        print("Weekly PDF →", pdf_path)
    return outfile
