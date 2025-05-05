# utils/email_utils.py
from __future__ import annotations
import smtplib
import ssl
import logging
import pathlib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from utils.secret import get as _secret  # you already have this helper

logger = logging.getLogger(__name__)


def send_pdf(to_email: str, pdf_path: str, *, subject: str, body: str) -> None:
    """
    Send a single PDF attachment via Gmail SMTP (STARTTLS, port 587).
    """
    msg = MIMEMultipart()
    msg["From"] = _secret("FROM_EMAIL", default=_secret("SMTP_USER"))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # ---- attach PDF -----------------------------------------------------
    fname = pathlib.Path(pdf_path).name
    with open(pdf_path, "rb") as fp:
        part = MIMEApplication(fp.read(), _subtype="pdf")
    part.add_header("Content-Disposition", "attachment", filename=fname)
    msg.attach(part)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(_secret("SMTP_HOST"), int(_secret("SMTP_PORT"))) as server:
            server.starttls(context=context)
            server.login(_secret("SMTP_USER"), _secret("SMTP_PASS"))
            server.sendmail(msg["From"], [to_email], msg.as_string())
        logger.info("📧 PDF emailed to %s", to_email)
    except Exception as e:
        logger.error("Email sending failed: %s", e)
        raise RuntimeError("Failed to send email") from e
