from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

class ContactRequest(BaseModel):
    name: str = Field(..., description="Sender name")
    email: str = Field(..., description="Sender email")
    subject: str = Field(..., description="Subject")
    message: str = Field(..., description="Message")
    to: Optional[str] = Field(None, description="Optional destination override")
    hp: Optional[str] = Field(None, description="Honeypot field for bots")

    @field_validator("email", "to")
    @classmethod
    def validate_emails(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
            raise ValueError("Invalid email format")
        return v

class ContactResponse(BaseModel):
    status: str
    message: Optional[str] = None
