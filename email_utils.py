import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Iterable, Optional

logger = logging.getLogger(__name__)


def send_email_to_address(
    to_emails: str | Iterable[str],
    subject: str,
    body: str,
    cc_emails: Optional[Iterable[str]] = None,
    from_name: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
) -> str:
    """Send an email via Gmail using SMTP_SSL.

    to_emails can be a single email string or an iterable of emails.
    Returns a human-readable message on success or raises an exception.
    """
    from_email = os.getenv("EMAIL_USERNAME") or os.getenv("GMAIL_USER")
    app_password = os.getenv("EMAIL_APP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
    from_name = from_name or os.getenv("EMAIL_FROM_NAME") or "Nevira Assistant"
    smtp_host = smtp_host or os.getenv("EMAIL_SMTP_HOST") or "smtp.gmail.com"
    smtp_port = smtp_port or int(os.getenv("EMAIL_SMTP_PORT") or 465)

    if not from_email or not app_password:
        msg = "Email configuration missing: set EMAIL_USERNAME and EMAIL_APP_PASSWORD."
        logger.error(msg)
        raise RuntimeError(msg)

    # Normalize recipients
    if isinstance(to_emails, str):
        to_list = [to_emails]
    else:
        to_list = list(to_emails)

    cc_list = list(cc_emails) if cc_emails else []

    # Build message
    msg = MIMEMultipart()
    try:
        msg["From"] = formataddr((from_name, from_email))
    except Exception:
        msg["From"] = from_email
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Subject"] = subject or "(no subject)"

    # Attach plain text body with utf-8
    body_text = body or ""
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    # Send via secure SMTP SSL
    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
            server.login(from_email, app_password)
            recipients = to_list + cc_list
            server.sendmail(from_email, recipients, msg.as_string())
    except smtplib.SMTPAuthenticationError as e:
        logger.exception("SMTP authentication failed")
        raise
    except Exception:
        logger.exception("Failed to send email")
        raise

    return f"Email sent successfully to {', '.join(to_list)}"
