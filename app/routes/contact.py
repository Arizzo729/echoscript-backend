from __future__ import annotations
import os
from fastapi import APIRouter, HTTPException, status
from app.schemas.contact import ContactRequest, ContactResponse
from app.utils.send_email import send_email, EmailError

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
    if request.hp:  # bot trap
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
        return ContactResponse(status="success", message="Thanks! We’ll get back to you soon.")
    except EmailError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send: {e}")
