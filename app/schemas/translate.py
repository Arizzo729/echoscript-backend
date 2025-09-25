from pydantic import BaseModel


class TranslateRequest(BaseModel):
    transcript_id: int
    target_language: str  # e.g. "es", "fr", "de"


class TranslateResponse(BaseModel):
    transcript_id: int
    target_language: str
    content: str
