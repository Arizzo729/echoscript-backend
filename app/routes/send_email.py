# utils/send_email.py — EchoScript.AI Email Helper

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.utils.logger import logger

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "support@echoscriptai.com")

def send_email(to: str, subject: str, content: str) -> dict:
    if not SENDGRID_API_KEY:
        logger.error("Missing SENDGRID_API_KEY environment variable.")
        return {"status": "error", "message": "Missing SendGrid API key."}

    if not to or not subject or not content:
        logger.warning("Attempted to send email with missing fields.")
        return {"status": "error", "message": "Invalid email parameters."}

    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to,
            subject=subject,
            plain_text_content=content
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"📧 Email sent to {to} | Status: {response.status_code}")
        return {"status": "success", "code": response.status_code}
    except Exception as e:
        logger.error(f"❌ Email send failed to {to}: {e}")
        return {"status": "error", "message": str(e)}
