from pydantic import BaseModel, EmailStr, Field


class ContactRequest(BaseModel):
    name: str = Field(
        ..., description="Name of the person sending the message", examples=["John Doe"]
    )
    email: EmailStr = Field(
        ...,
        description="Email address of the sender",
        examples=["john.doe@example.com"],
    )
    subject: str = Field(
        ..., description="Subject of the message", examples=["Issue with my account"]
    )
    message: str = Field(
        ...,
        description="Content of the message",
        examples=["Hello, I have an issue with my account and need assistance."],
    )


class ContactResponse(BaseModel):
    status: str = Field(
        ...,
        description="Result of the contact submission (e.g., success or error)",
        examples=["success"],
    )
    message: str | None = Field(
        None,
        description="Optional detail or thank-you message",
        examples=["Thank you for contacting us! We will get back to you soon."],
    )
