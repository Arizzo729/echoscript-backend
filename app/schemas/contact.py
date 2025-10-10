from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class ContactRequest(BaseModel):
    name: str = Field(..., description="Sender name", examples=["John Doe"])
    email: EmailStr = Field(..., description="Sender email", examples=["john.doe@example.com"])
    subject: str = Field(..., description="Subject", examples=["Issue with my account"])
    message: str = Field(..., description="Message text")
    # optional override; if not set we’ll use env default (support@echoscript.ai)
    to: Optional[EmailStr] = Field(None, description="Optional destination override")
    # honeypot (from frontend)
    hp: Optional[str] = Field(None, description="Honeypot field for bots")

class ContactResponse(BaseModel):
    status: str = Field(..., description="Result (success or error)", examples=["success"])
    message: Optional[str] = Field(None, description="Optional detail/thank-you")

