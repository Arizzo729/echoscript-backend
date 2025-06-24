from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from models.newsletter import NewsletterSubscriber
from schemas.newsletter import (
    NewsletterSubscribeRequest,
    NewsletterSubscribeResponse,
    NewsletterUnsubscribeResponse,
)
from database import get_db
from fastapi.responses import HTMLResponse

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
    Subscribe an email to the EchoScript.AI newsletter.
    """
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

    return NewsletterSubscribeResponse(
        email=new_subscriber.email,
        subscribed_at=new_subscriber.subscribed_at,
        message="Successfully subscribed to the newsletter."
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
            detail="Email not found in the subscriber list."
        )

    db.delete(subscriber)
    db.commit()

    return NewsletterUnsubscribeResponse(
        email=request.email,
        message="You have been unsubscribed from the newsletter."
    )


@router.get("/confirm", response_class=HTMLResponse)
def confirm_newsletter_subscription(
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Confirm a newsletter subscription via email link.
    """
    subscriber = db.query(NewsletterSubscriber).filter_by(email=email).first()
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found for this email."
        )

    # Future: Update `confirmed = True` if such a column exists

    return HTMLResponse(content=f"""
        <html>
          <head><title>Newsletter Confirmation</title></head>
          <body style="font-family:sans-serif;text-align:center;margin-top:50px;">
            <h2>✅ You're now subscribed to the EchoScript.AI newsletter!</h2>
            <p>Email: <strong>{email}</strong></p>
            <p>Thank you for joining us. Expect great updates soon.</p>
          </body>
        </html>
    """)

