from pydantic import BaseModel, EmailStr, Field


class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr = Field(
        default=...,
        description="Email address to subscribe to the newsletter",
        example="user@example.com",
    )


class NewsletterUnsubscribeRequest(BaseModel):
    email: EmailStr = Field(
        default=...,
        description="Email address to remove from the newsletter list",
        example="user@example.com",
    )


class NewsletterResponse(BaseModel):
    status: str = Field(
        default=...,
        description="Operation status (e.g., 'subscribed', 'unsubscribed')",
        example="subscribed",
    )


__all__ = [
    "NewsletterSubscribeRequest",
    "NewsletterUnsubscribeRequest",
    "NewsletterResponse",
]
