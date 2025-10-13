# app/routes/email_test.py
from fastapi import APIRouter, HTTPException
from app.utils.send_email import send_email, EmailError
from app.core.settings import settings

router = APIRouter(prefix="/email-test", tags=["Development"])

@router.post("/", summary="Send a test email")
async def send_test_email():
    """
    Sends a test email using the configured email provider (Resend or SMTP).
    This is a utility endpoint for developers to verify email configuration.
    """
    to = settings.CONTACT_TO
    try:
        send_email(
            to_address=to,
            subject="EchoScript Test Email",
            body_text="This is a test email from the EchoScript API.",
            body_html="<p>This is a test email from the <strong>EchoScript API</strong>.</p>",
        )
        return {"ok": True, "message": f"Test email sent to {to}"}
    except EmailError as e:
        raise HTTPException(status_code=500, detail=str(e))