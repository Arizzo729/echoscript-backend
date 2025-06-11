import os
import smtplib
from email.message import EmailMessage
from app.utils.logger import logger

def send_email(to_email: str, subject: str, body: str):
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not email_address or not email_password:
        logger.error("❌ Missing EMAIL_ADDRESS or EMAIL_PASSWORD environment variables.")
        raise ValueError("Email credentials not configured properly.")

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = email_address
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)

        logger.info(f"📧 Email sent to {to_email} — Subject: {subject}")

    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {e}")
        raise
