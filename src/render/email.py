import os, smtplib, ssl, zipfile, tempfile
from email.message import EmailMessage
from pathlib import Path

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT  = os.getenv("EMAIL_TO")

def send(pdf_paths: list[Path]):
    """Send all 4 PDFs in ONE e-mail, zipped."""
    msg = EmailMessage()
    week = pdf_paths[0].stem.split("-")[0]   # 2025-W21
    msg["Subject"] = f"African Crime Weekly – {week}"
    msg["From"]    = f"Africa Intelligence <{GMAIL_USER}>"
    msg["To"]      = RECIPIENT
    msg.set_content(
        "Please find the African Crime Weekly intelligence briefs "
        f"for week {week} attached (zipped).\n\n"
        "Reports: Terrorism & Violent Extremism, Organised Crime, "
        "Financial Crime, Cyber Crime.\n\n"
        "This is an automated product – contents do not reflect "
        "the opinion of the author(s).\n\n"
        "African Union – African Crime Weekly (ACW)"
    )

    # create in-memory zip
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in pdf_paths:
                zf.write(p, p.name)
        tmp.flush()
        zip_data = Path(tmp.name).read_bytes()

    msg.add_attachment(zip_data, maintype="application", subtype="zip",
                       filename=f"{week}-African-Crime-Weekly.zip")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
    print(f"E-mailed {len(pdf_paths)} reports in one ZIP to {RECIPIENT}")
