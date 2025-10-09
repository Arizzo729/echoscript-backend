from fastapi import APIRouter, HTTPException, status
from app.schemas.contact import ContactRequest, ContactResponse
from app.utils.send_email import send_email

# relative prefix (no /api)
router = APIRouter(prefix="/contact", tags=["Contact"])

@router.post("/", response_model=ContactResponse, summary="Send a message to support")
def contact(request: ContactRequest) -> ContactResponse:
    try:
        send_email(
            to_address=request.to or "support@echoscript.ai",
            subject=f"[Contact] {request.subject}",
            body=f"From: {request.email}\n\n{request.message}",
        )
        return ContactResponse(ok=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send: {e}",
        )
