# app/utils/send_email.py
from __future__ import annotations
import smtplib
import ssl
from email.message import EmailMessage
from typing import Sequence

import httpx

from app.core.settings import settings
from app.utils.logger import logger

class EmailError(RuntimeError):
    """Custom exception for email sending failures."""
    pass

def send_email(
    to_address: str | Sequence[str],
    subject: str,
    body_text: str,
    body_html: str | None = None,
    reply_to: str | None = None,
) -> None:
    """
    Sends an email using the configured provider (Resend or SMTP).

    - Prioritizes Resend if RESEND_API_KEY is set.
    - Falls back to SMTP if SMTP settings are provided.
    - Raises EmailError if no provider is configured or if sending fails.
    """
    # --- HTTP Provider (Resend) ---
    if settings.RESEND_API_KEY:
        try:
            with httpx.Client() as client:
                payload = {
                    "from": settings.RESEND_FROM,
                    "to": to_address if isinstance(to_address, list) else [to_address],
                    "subject": subject,
                    "text": body_text,
                    "html": body_html,
                    "reply_to": reply_to,
                }
                headers = {
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                }
                response = client.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                logger.info(f"Email sent to {to_address} via Resend.")
                return
        except httpx.HTTPStatusError as e:
            logger.error(f"Resend API error: {e.response.status_code} - {e.response.text}")
            raise EmailError(f"Failed to send email via Resend: {e.response.text}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred with Resend: {e}")
            raise EmailError("An unexpected error occurred with the email service.") from e

    # --- SMTP Fallback ---
    if all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASS]):
        try:
            msg = EmailMessage()
            msg["From"] = settings.SMTP_FROM
            msg["To"] = to_address if isinstance(to_address, str) else ", ".join(to_address)
            msg["Subject"] = subject
            if reply_to:
                msg["Reply-To"] = reply_to
            
            msg.set_content(body_text)
            if body_html:
                msg.add_alternative(body_html, subtype="html")

            context = ssl.create_default_context()
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
                server.starttls(context=context)
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.send_message(msg)
                logger.info(f"Email sent to {to_address} via SMTP.")
                return
        except Exception as e:
            logger.error(f"SMTP sending failed: {e}")
            raise EmailError("Failed to send email via SMTP.") from e

    # --- No Provider Configured ---
    logger.error("Email sending failed: No email provider is configured.")
    raise EmailError("Email service is not configured.")