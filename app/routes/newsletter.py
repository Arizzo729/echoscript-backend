# app/routes/newsletter.py
from fastapi import APIRouter

from app.schemas.newsletter import (
    NewsletterResponse,
    NewsletterSubscribeRequest,
    NewsletterUnsubscribeRequest,
)

router = APIRouter(prefix="/api/newsletter", tags=["Newsletter"])


@router.post("/subscribe", response_model=NewsletterResponse)
def subscribe(_: NewsletterSubscribeRequest) -> NewsletterResponse:
    # Minimal stub: always succeed (no Redis/email deps)
    return NewsletterResponse(status="subscribed")


@router.post("/unsubscribe", response_model=NewsletterResponse)
def unsubscribe(_: NewsletterUnsubscribeRequest) -> NewsletterResponse:
    # Minimal stub: always succeed
    return NewsletterResponse(status="unsubscribed")
