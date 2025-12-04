#!/usr/bin/env python3
"""
test_email.py

Quick test script to send a test email using env vars:
  GMAIL_USER
  GMAIL_APP_PASSWORD

Run from your activated venv at project root:
  python test_email.py
"""
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
import sys
from typing import cast

load_dotenv()

EMAIL = os.getenv("GMAIL_USER")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

print("Debug: GMAIL_USER found?", bool(EMAIL))
print("Debug: GMAIL_APP_PASSWORD found?", bool(APP_PASSWORD))

# Validate early so type-checkers (Pylance) know these are non-None below
if not EMAIL or not APP_PASSWORD:
    print("\nERROR: Missing credentials. Make sure .env has:")
    print("  GMAIL_USER=you@example.com")
    print("  GMAIL_APP_PASSWORD=your-app-password\n")
    sys.exit(1)

# Reassign to help type checker understand these are now guaranteed to be strings
email: str = EMAIL  # type: ignore
app_password: str = APP_PASSWORD  # type: ignore

# Build a minimal plain-text message
msg = MIMEText("This is a test email sent from Nevira SMTP test script.")
msg["Subject"] = "Nevira SMTP Test"
msg["From"] = email
msg["To"] = email

def send_via_ssl() -> bool:
    """Try SMTP over SSL (port 465)."""
    try:
        print("Trying SMTP_SSL (smtp.gmail.com:465)...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            # Pylance now knows email and app_password are str
            server.login(email, app_password)
            server.sendmail(email, [email], msg.as_string())
        print("Email sent successfully via SSL (465).")
        return True
    except Exception as e:
        print("SMTP_SSL error:", repr(e))
        return False

def send_via_starttls() -> bool:
    """Try SMTP with STARTTLS (port 587)."""
    try:
        print("Trying STARTTLS (smtp.gmail.com:587)...")
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email, app_password)
            server.sendmail(email, [email], msg.as_string())
        print("Email sent successfully via STARTTLS (587).")
        return True
    except Exception as e:
        print("STARTTLS error:", repr(e))
        return False

if __name__ == "__main__":
    ok = send_via_ssl()
    if not ok:
        if not send_via_starttls():
            print("\nBoth methods failed. See errors above.")
            print("Common issues:")
            print("- Wrong app password (recreate app password after enabling 2FA).")
            print("- Network blocking outbound SMTP ports (try a different network).")
            print("- Account security blocking sign-ins (check Gmail security alerts).")
            sys.exit(2)
