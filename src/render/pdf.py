from weasyprint import HTML
import datetime as dt, pathlib as pl

def render(html: str, pillar: str, start: dt.datetime):
    outfile = pl.Path(f"{start.strftime('%Y-W%U')}-{pillar}.pdf")
    HTML(string=f"<h1>{pillar}</h1><pre>{html}</pre>").write_pdf(outfile)
    return outfile
