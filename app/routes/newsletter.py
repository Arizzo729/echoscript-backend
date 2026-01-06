from fastapi import APIRouter
from app.schemas.newsletter import (
    NewsletterResponse,
    NewsletterSubscribeRequest,
    NewsletterUnsubscribeRequest,
)

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])

@router.post("/subscribe", response_model=NewsletterResponse)
def subscribe(_: NewsletterSubscribeRequest) -> NewsletterResponse:
    return NewsletterResponse(status="subscribed")

@router.post("/unsubscribe", response_model=NewsletterResponse)
def unsubscribe(_: NewsletterUnsubscribeRequest) -> NewsletterResponse:
    return NewsletterResponse(status="unsubscribed")
