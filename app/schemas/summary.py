# === app/schemas/summary.py ===
from pydantic import BaseModel


class SummaryRequest(BaseModel):
    transcript_id: int


class SummaryResponse(BaseModel):
    transcript_id: int
    summary: str
