# app/routes/email_test.py
import os
from fastapi import APIRouter, HTTPException
from app.utils.send_email import send_email, EmailError

router = APIRouter(prefix="/contact", tags=["contact"])

@router.post("/test")
async def contact_test():
    to = os.getenv("RESEND_TO") or os.getenv("SMTP_TO") or "support@echoscript.ai"
    try:
        send_email(
            to_address=to,
            subject="EchoScript email test",
            body_text="If you see this, HTTP email is working ✅",
            body_html="<p>If you see this, <b>HTTP email</b> is working ✅</p>",
        )
        return {"ok": True, "to": to}
    except EmailError as e:
        raise HTTPException(status_code=500, detail=str(e))
