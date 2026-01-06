from __future__ import annotations
import os, json, smtplib, ssl, http.client, logging
from email.message import EmailMessage
from typing import Iterable, Optional, Sequence

log = logging.getLogger("echoscript")

class EmailError(RuntimeError): ...

def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if (v is not None and v.strip() != "") else default

def _ensure_list(v: Optional[Iterable[str]]) -> list[str]:
    if not v: return []
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
    api_key = _env("RESEND_API_KEY")
    from_display = _env("EMAIL_FROM") or _env("RESEND_FROM") or _env("SMTP_FROM") or "EchoScript <noreply@onresend.com>"
    to_list = _ensure_list([to_address] if isinstance(to_address, str) else to_address)
    cc_list = _ensure_list(cc); bcc_list = _ensure_list(bcc)

    # HTTP providers (Resend -> SendGrid) first
    if api_key:
        log.info("EMAIL_MODE=HTTP provider=resend to=%s", ",".join(to_list))
        # ... (rest of resend logic)
        # ...
        
    # SendGrid HTTP provider
    sg_api_key = _env("SENDGRID_API_KEY")
    if sg_api_key:
        try:
            log.info("EMAIL_MODE=HTTP provider=sendgrid to=%s", ",".join(to_list))
            # If from_display is a full string like "EchoScript <noreply@onresend.com>", 
            # SendGrid might need just the email. 
            # Let's try to extract email if it's in "Name <email>" format.
            from_email = from_display
            if "<" in from_display and ">" in from_display:
                from_email = from_display.split("<")[1].split(">")[0]
            
            payload = {
                "personalizations": [{"to": [{"email": t} for t in to_list]}],
                "from": {"email": from_email, "name": from_display.split("<")[0].strip() if "<" in from_display else "EchoScript"},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body_text or ""}],
            }
            if body_html:
                payload["content"].append({"type": "text/html", "value": body_html})
            if reply_to:
                payload["reply_to"] = {"email": reply_to}
            
            conn = http.client.HTTPSConnection("api.sendgrid.com", timeout=15)
            conn.request("POST", "/v3/mail/send", body=json.dumps(payload),
                         headers={"Authorization": f"Bearer {sg_api_key}", "Content-Type": "application/json"})
            res = conn.getresponse()
            data = res.read().decode("utf-8", errors="ignore")
            if res.status >= 300:
                log.error(f"SendGrid error {res.status}: {data}")
                raise EmailError(f"SendGrid error {res.status}: {data}")
            log.info("Email sent successfully via SendGrid")
            return
        except Exception as e:
            if isinstance(e, EmailError): raise
            log.exception(f"SendGrid HTTP email send failed: {e}")
            raise EmailError(f"SendGrid HTTP email send failed: {e}") from e

    raise EmailError("No email provider configured (set RESEND_API_KEY, SENDGRID_API_KEY, or SMTP_* envs).")
