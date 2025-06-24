from pydantic import BaseModel, EmailStr
from datetime import datetime

class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr

class NewsletterSubscribeResponse(BaseModel):
    email: EmailStr
    subscribed_at: datetime
    message: str

class NewsletterUnsubscribeResponse(BaseModel):
    email: EmailStr
    message: str

class NewsletterConfirmRequest(BaseModel):
    token: str

class NewsletterConfirmResponse(BaseModel):
    email: EmailStr
    message: str