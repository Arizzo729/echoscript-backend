from fastapi import APIRouter
from app.schemas.newsletter import (
    NewsletterResponse,
    NewsletterSubscribeRequest,
    NewsletterUnsubscribeRequest,
)

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])

@router.post("/subscribe", response_model=NewsletterResponse)
def subscribe(request: NewsletterSubscribeRequest) -> NewsletterResponse:
    # Logic to subscribe the email would go here
    return NewsletterResponse(status="subscribed", message="Successfully subscribed to newsletter")

@router.post("/unsubscribe", response_model=NewsletterResponse)
def unsubscribe(request: NewsletterUnsubscribeRequest) -> NewsletterResponse:
    # Logic to unsubscribe the email would go here
    return NewsletterResponse(status="unsubscribed", message="Successfully unsubscribed from newsletter")
