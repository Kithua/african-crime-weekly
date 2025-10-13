import os, smtplib, ssl
from email.message import EmailMessage
from pathlib import Path

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT  = os.getenv("EMAIL_TO")

def send(pdf_path: Path):
    msg = EmailMessage()
    msg["Subject"] = f"African Crime Weekly – {pdf_path.stem}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = RECIPIENT
    msg.set_content("Please find the weekly intelligence brief attached.")

    pdf_data = pdf_path.read_bytes()
    msg.add_attachment(pdf_data, maintype="application", subtype="pdf",
                       filename=pdf_path.name)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        print("DEBUG: user=", repr(GMAIL_USER), "pwd=", repr(GMAIL_PASS and len(GMAIL_PASS)))
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
    print(f"E-mailed {pdf_path.name} to {RECIPIENT}")
