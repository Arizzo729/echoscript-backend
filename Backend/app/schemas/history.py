# === app/schemas/history.py ===
from datetime import datetime
from typing import List

from pydantic import BaseModel


class HistoryItem(BaseModel):
    timestamp: datetime
    user_id: int
    change: str  # e.g. "Edited paragraph 2"


class HistoryRequest(BaseModel):
    transcript_id: int


class HistoryResponse(BaseModel):
    transcript_id: int
    history: List[HistoryItem]
