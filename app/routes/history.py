# ---- EchoScript.AI: routes/history.py ----

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from app.utils.redis_client import redis_client
from app.utils.logger import logger
import json

router = APIRouter(prefix="/history", tags=["History"])

# ---- History Entry Model ----
class HistoryEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    transcript_id: str
    summary: str
    tags: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ---- Add New Entry (Auto-Expire in 30 Days) ----
@router.post("/add", response_model=dict)
async def add_history(entry: HistoryEntry):
    key = f"history:{entry.user_id}:{entry.transcript_id}"
    redis_client.setex(key, timedelta(days=30), json.dumps(entry.dict()))
    logger.info(f"🗂️ Saved history for user={entry.user_id}, transcript={entry.transcript_id}")
    return {"message": "History saved", "entry_id": str(entry.id)}

# ---- Fetch All History by User ----
@router.get("/all/{user_id}", response_model=List[HistoryEntry])
async def get_history(user_id: str):
    pattern = f"history:{user_id}:*"
    keys = redis_client.keys(pattern)

    entries = []
    for key in keys:
        raw = redis_client.get(key)
        if raw:
            data = json.loads(raw)
            entries.append(HistoryEntry(**data))
    return sorted(entries, key=lambda x: x.timestamp, reverse=True)

# ---- Delete Specific Transcript History ----
@router.delete("/delete/{user_id}/{transcript_id}", response_model=dict)
async def delete_entry(user_id: str, transcript_id: str):
    key = f"history:{user_id}:{transcript_id}"
    deleted = redis_client.delete(key)
    logger.info(f"🗑️ Deleted transcript={transcript_id} for user={user_id}")
    return {"message": "Deleted" if deleted else "Not found", "transcript_id": transcript_id}

