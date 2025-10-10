# app/utils/send_email.py
from __future__ import annotations

import os
import json
import smtplib
import ssl
import http.client
from email.message import EmailMessage
from typing import Iterable, Optional, Sequence


class EmailError(RuntimeError):
    pass


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    return val if (val is not None and val.strip() != "") else default


def _ensure_list(v: Optional[Iterable[str]]) -> list[str]:
    if not v:
        return []
    return [s for s in v if s and s.strip()]


def send_email(
    to_address: str | Sequence[str],
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    cc: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
    reply_to: Optional[str] = None,
) -> None:
    """
    Send an email using an HTTP API (Resend) if configured; otherwise try SMTP as a fallback.
    Raises EmailError on failure.
    """

    # Prefer HTTP provider (Resend)
    api_key = _env("RESEND_API_KEY")
    from_display = _env("EMAIL_FROM") or _env("RESEND_FROM") or _env("SMTP_FROM") or "EchoScript <noreply@onresend.com>"
    to_list = _ensure_list([to_address] if isinstance(to_address, str) else to_address)
    cc_list = _ensure_list(cc)
    bcc_list = _ensure_list(bcc)

    if api_key:
        try:
            payload = {
                "from": from_display,
                "to": to_list,
                "subject": subject,
                "text": body_text,
            }
            if body_html:
                payload["html"] = body_html
            if cc_list:
                payload["cc"] = cc_list
            if bcc_list:
                payload["bcc"] = bcc_list
            if reply_to:
                payload["reply_to"] = reply_to

            conn = http.client.HTTPSConnection("api.resend.com", timeout=15)
            conn.request(
                "POST",
                "/emails",
                body=json.dumps(payload),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
            res = conn.getresponse()
            data = res.read().decode("utf-8", errors="ignore")
            if res.status >= 300:
                raise EmailError(f"Resend error {res.status}: {data}")
            return
        except Exception as e:
            raise EmailError(f"HTTP email send failed: {e}") from e

    # Fallback: SMTP (often blocked on PaaS, but works locally)
    host = _env("SMTP_HOST")
    port = int(_env("SMTP_PORT", "587"))
    user = _env("SMTP_USER")
    pwd = _env("SMTP_PASS")
    smtp_from = _env("SMTP_FROM", from_display)

    if host and user and pwd:
        try:
            msg = EmailMessage()
            msg["From"] = smtp_from
            msg["To"] = ", ".join(to_list)
            if cc_list:
                msg["Cc"] = ", ".join(cc_list)
            msg["Subject"] = subject
            if reply_to:
                msg["Reply-To"] = reply_to

            if body_html:
                msg.set_content(body_text or "")
                msg.add_alternative(body_html, subtype="html")
            else:
                msg.set_content(body_text or "")

            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.ehlo()
                s.starttls(context=context)
                s.login(user, pwd)
                recipients = to_list + cc_list + bcc_list
                s.send_message(msg, from_addr=smtp_from, to_addrs=recipients)
            return
        except Exception as e:
            raise EmailError(f"SMTP send failed: {e}") from e

    raise EmailError("No email provider configured (set RESEND_API_KEY or SMTP_* envs).")

