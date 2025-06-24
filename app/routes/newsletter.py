# routes/newsletter.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.newsletter import NewsletterSubscriber
from schemas.newsletter import NewsletterSubscribeRequest
from database import get_db

router = APIRouter(
    prefix="/newsletter",
    tags=["Newsletter"],
    responses={404: {"description": "Not found"}}
)

@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe_to_newsletter(
    request: NewsletterSubscribeRequest,
    db: Session = Depends(get_db)
):
    existing = db.query(NewsletterSubscriber).filter_by(email=request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already subscribed to the newsletter."
        )

    new_subscriber = NewsletterSubscriber(email=request.email)
    db.add(new_subscriber)
    db.commit()
    db.refresh(new_subscriber)
    return {
        "message": "Successfully subscribed to the newsletter.",
        "email": new_subscriber.email,
        "subscribed_at": new_subscriber.subscribed_at
    }

@router.delete("/unsubscribe", status_code=status.HTTP_200_OK)
def unsubscribe_from_newsletter(
    request: NewsletterSubscribeRequest,
    db: Session = Depends(get_db)
):
    subscriber = db.query(NewsletterSubscriber).filter_by(email=request.email).first()
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found in the subscriber list."
        )

    db.delete(subscriber)
    db.commit()
    return {
        "message": "You have been unsubscribed from the newsletter.",
        "email": request.email
    }

