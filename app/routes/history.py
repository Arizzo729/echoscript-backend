from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json

from app.utils.redis_client import redis_client
from app.utils.logger import logger

router = APIRouter(prefix="/history", tags=["History"])

# === History Schema ===
class HistoryEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    transcript_id: str
    summary: str
    tags: List[str] = []
    language: Optional[str] = None
    source: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# === Store Transcript History (30 Days Expiry) ===
@router.post("/add", response_model=dict)
async def save_history(entry: HistoryEntry):
    try:
        key = f"history:{entry.user_id}:{entry.transcript_id}"
        redis_client.setex(key, timedelta(days=30), json.dumps(entry.dict()))
        logger.info(f"[History] ✅ Saved | user={entry.user_id} | transcript={entry.transcript_id}")
        return {"message": "History saved successfully.", "entry_id": str(entry.id)}
    except Exception as e:
        logger.exception(f"[History Error] Save failed: {e}")
        raise HTTPException(status_code=500, detail="Unable to save transcript history.")

# === Retrieve User History ===
@router.get("/all/{user_id}", response_model=List[HistoryEntry])
async def fetch_user_history(user_id: str):
    try:
        pattern = f"history:{user_id}:*"
        keys = redis_client.keys(pattern)

        entries = []
        for key in keys:
            raw = redis_client.get(key)
            if raw:
                try:
                    data = json.loads(raw)
                    entries.append(HistoryEntry(**data))
                except Exception as parse_err:
                    logger.warning(f"[History Parse] Failed to parse {key}: {parse_err}")

        return sorted(entries, key=lambda x: x.timestamp, reverse=True)
    except Exception as e:
        logger.exception(f"[History Fetch] Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history.")

# === Delete Specific History Entry ===
@router.delete("/delete/{user_id}/{transcript_id}", response_model=dict)
async def delete_history_entry(user_id: str, transcript_id: str):
    try:
        key = f"history:{user_id}:{transcript_id}"
        deleted = redis_client.delete(key)
        logger.info(f"[History Delete] user={user_id} | transcript={transcript_id} | deleted={bool(deleted)}")
        return {
            "message": "Entry deleted successfully." if deleted else "Entry not found.",
            "transcript_id": transcript_id,
            "deleted": bool(deleted)
        }
    except Exception as e:
        logger.exception(f"[History Delete] Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete history entry.")

