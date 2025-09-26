import smtplib
from email.message import EmailMessage

from app.config import config
from app.utils.logger import logger


def send_email(
    to_address: str, subject: str, body: str, html: str | None = None
) -> None:
    """
    Send an email using SMTP credentials defined in the environment.

    Args:
        to_address: Recipient email address
        subject: Email subject
        body: Plain-text email body
        html: Optional HTML content for rich emails

    Raises:
        RuntimeError: if email credentials are not configured or sending fails
    """
    # Retrieve SMTP settings from config
    smtp_user = config.EMAIL_ADDRESS
    smtp_pass = config.EMAIL_PASSWORD
    smtp_host = config.SMTP_HOST or "smtp.gmail.com"
    smtp_port = config.SMTP_PORT or 587

    if not smtp_user or not smtp_pass:
        raise RuntimeError(
            "SMTP credentials (EMAIL_ADDRESS and EMAIL_PASSWORD) are required to send email"
        )

    # Construct the message
    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    # Send via SMTP
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info(f"Email sent to {to_address}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_address}: {e}")
        raise RuntimeError(f"Error sending email: {e}")


__all__ = ["send_email"]
