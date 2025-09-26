import logging

from fastapi import APIRouter, HTTPException, status

from app.config import config
from app.schemas.contact import ContactRequest, ContactResponse
from app.utils.send_email import send_email

router = APIRouter()
logger = logging.getLogger("echoscript")


@router.post(
    "/", response_model=ContactResponse, summary="Submit a contact form message"
)
async def submit_contact(request: ContactRequest) -> ContactResponse:
    """
    Receive a contact form submission and email it to the support address.
    """
    subject = f"[Contact] {request.subject} from {request.name}"
    body = (
        f"Name: {request.name}\n"
        f"Email: {request.email}\n\n"
        f"Message:\n{request.message}"
    )
    try:
        # Send to the configured support email
        support_email = getattr(config, "SUPPORT_EMAIL", None) or config.EMAIL_ADDRESS
        send_email(to_address=support_email, subject=subject, body=body)
        return ContactResponse(status="sent")
    except Exception as e:
        logger.error(f"Failed to process contact form: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send contact message at this time",
        )
