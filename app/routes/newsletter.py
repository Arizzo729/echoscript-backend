from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse

from models.newsletter import NewsletterSubscriber
from schemas.newsletter import (
    NewsletterSubscribeRequest,
    NewsletterSubscribeResponse,
    NewsletterUnsubscribeResponse,
)
from database import get_db

router = APIRouter(
    prefix="/newsletter",
    tags=["Newsletter"],
    responses={404: {"description": "Not found"}}
)

@router.post("/subscribe", response_model=NewsletterSubscribeResponse, status_code=status.HTTP_201_CREATED)
def subscribe_to_newsletter(
    request: NewsletterSubscribeRequest,
    db: Session = Depends(get_db)
):
    """
    Subscribe an email to the EchoScript.AI newsletter with duplicate prevention.
    """
    existing = db.query(NewsletterSubscriber).filter_by(email=request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already subscribed."
        )

    new_subscriber = NewsletterSubscriber(email=request.email)
    db.add(new_subscriber)
    db.commit()
    db.refresh(new_subscriber)

    return NewsletterSubscribeResponse(
        email=new_subscriber.email,
        subscribed_at=new_subscriber.subscribed_at,
        message="🎉 Subscription successful. You're now on the list!"
    )


@router.delete("/unsubscribe", response_model=NewsletterUnsubscribeResponse, status_code=status.HTTP_200_OK)
def unsubscribe_from_newsletter(
    request: NewsletterSubscribeRequest,
    db: Session = Depends(get_db)
):
    """
    Unsubscribe an email from the EchoScript.AI newsletter.
    """
    subscriber = db.query(NewsletterSubscriber).filter_by(email=request.email).first()
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That email is not subscribed."
        )

    db.delete(subscriber)
    db.commit()

    return NewsletterUnsubscribeResponse(
        email=request.email,
        message="You've been successfully unsubscribed."
    )


@router.get("/confirm", response_class=HTMLResponse)
def confirm_newsletter_subscription(
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Confirm a newsletter subscription via email link (HTML response).
    """
    subscriber = db.query(NewsletterSubscriber).filter_by(email=email).first()
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for this email."
        )

    return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
            <meta charset=\"UTF-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
            <title>Newsletter Confirmed</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; text-align: center; margin-top: 80px; background: #f9fafb; }}
                h2 {{ color: #10b981; }}
                p {{ color: #374151; }}
            </style>
        </head>
        <body>
            <h2>✅ Subscription Confirmed</h2>
            <p><strong>{email}</strong> has been added to the EchoScript.AI newsletter list.</p>
            <p>Thank you for joining us. Expect great updates soon.</p>
        </body>
        </html>
    """)
