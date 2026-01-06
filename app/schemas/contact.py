from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class ContactRequest(BaseModel):
    name: str = Field(..., description="Sender name")
    email: EmailStr = Field(..., description="Sender email")
    subject: str = Field(..., description="Subject")
    message: str = Field(..., description="Message")
    to: Optional[EmailStr] = Field(None, description="Optional destination override")
    hp: Optional[str] = Field(None, description="Honeypot field for bots")

class ContactResponse(BaseModel):
    status: str
    message: Optional[str] = None
