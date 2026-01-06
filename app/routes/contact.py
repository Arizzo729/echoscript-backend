from __future__ import annotations
import os
import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.contact import ContactRequest, ContactResponse
from app.utils.send_email import send_email, EmailError

log = logging.getLogger("echoscript")

router = APIRouter(prefix="/contact", tags=["Contact"])

def _default_to() -> str:
    return os.getenv("RESEND_TO") or os.getenv("SMTP_TO") or os.getenv("CONTACT_TO") or "support@echoscript.ai"

def _body_text(req: ContactRequest) -> str:
    return (
        f"New contact submission\n\n"
        f"Name: {req.name}\n"
        f"Email: {req.email}\n"
        f"Subject: {req.subject}\n\n"
        f"{req.message}\n"
    )

def _body_html(req: ContactRequest) -> str:
    return (
        f"<h2>New contact submission</h2>"
        f"<p><b>Name:</b> {req.name}</p>"
        f"<p><b>Email:</b> {req.email}</p>"
        f"<p><b>Subject:</b> {req.subject}</p>"
        f"<hr/><pre style='white-space:pre-wrap'>{req.message}</pre>"
    )

@router.post("", response_model=ContactResponse)
@router.post("/", response_model=ContactResponse)
def contact(request: ContactRequest) -> ContactResponse:
    # Log incoming contact payload (omit honeypot/internal fields if present)
    try:
        payload = request.model_dump() if hasattr(request, "model_dump") else (request.dict() if hasattr(request, "dict") else {})
    except Exception:
        payload = {}
    safe_payload = {k: v for k, v in payload.items() if k != 'hp'}
    log.info("Contact request received: %s", safe_payload)
    try:
        log_dir = os.getenv('LOG_DIR') or os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        outpath = os.path.join(log_dir, 'contact_debug.log')
        with open(outpath, 'a', encoding='utf-8') as fh:
            fh.write(f"{__import__('datetime').datetime.utcnow().isoformat()}Z \"request\" " + str(safe_payload) + "\n")
    except Exception:
        pass

    if request.hp:  # bot trap
        log.info("Contact honeypot triggered, discarding request")
        return ContactResponse(status="success", message="Thanks!")

    try:
        to_addr = request.to or _default_to()
        send_email(
            to_address=to_addr,
            subject=f"[Contact] {request.subject}",
            body_text=_body_text(request),
            body_html=_body_html(request),
            reply_to=str(request.email),
        )
        log.info("Contact email queued/sent to %s for %s", to_addr, request.email)
        try:
            with open(os.path.join(os.getenv('LOG_DIR') or os.path.join(os.getcwd(),'logs'), 'contact_debug.log'), 'a', encoding='utf-8') as fh:
                fh.write(f"{__import__('datetime').datetime.utcnow().isoformat()}Z \"sent\" to={to_addr} from={request.email}\n")
        except Exception:
            pass
        return ContactResponse(status="success", message="Thanks! We’ll get back to you soon.")
    except EmailError as e:
        log.exception("send_email failed for contact: %s", e)
        try:
            with open(os.path.join(os.getenv('LOG_DIR') or os.path.join(os.getcwd(),'logs'), 'contact_debug.log'), 'a', encoding='utf-8') as fh:
                fh.write(f"{__import__('datetime').datetime.utcnow().isoformat()}Z \"error\" {str(e)}\n")
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send: {e}")
    except Exception as e:
        log.exception("Unexpected error handling contact: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
