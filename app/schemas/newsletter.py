from pydantic import BaseModel, Field, field_validator
import re

class NewsletterSubscribeRequest(BaseModel):
    email: str = Field(
        ...,
        description="Email address to subscribe to the newsletter",
        json_schema_extra={"example": "user@example.com"},
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Simple permissive regex: user@domain.tld
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
            raise ValueError("Invalid email format")
        return v


class NewsletterUnsubscribeRequest(BaseModel):
    email: str = Field(
        ...,
        description="Email address to remove from the newsletter list",
        json_schema_extra={"example": "user@example.com"},
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
            raise ValueError("Invalid email format")
        return v


class NewsletterResponse(BaseModel):
    status: str = Field(
        ...,
        description="Operation status (e.g., 'subscribed', 'unsubscribed')",
        json_schema_extra={"example": "subscribed"},
    )
    message: str = Field(
        default="Success",
        description="Detailed message about the result",
    )


__all__ = [
    "NewsletterSubscribeRequest",
    "NewsletterUnsubscribeRequest",
    "NewsletterResponse",
]
