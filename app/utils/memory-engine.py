# ---- EchoScript.AI: utils/memory_engine.py ----

from datetime import datetime
from typing import List, Dict
from uuid import uuid4
from app.utils.logger import logger

class EchoMemory:
    def __init__(self, max_memory_per_user: int = 10):
        self.memory: List[Dict] = []
        self.max_per_user = max_memory_per_user

    def add(self, user_id: str, text: str) -> None:
        entry = {
            "id": str(uuid4()),
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "text": text
        }
        self.memory.append(entry)

        # Keep only the latest N entries for each user
        user_entries = [m for m in self.memory if m["user_id"] == user_id]
        if len(user_entries) > self.max_per_user:
            self.memory = [
                m for m in self.memory
                if not (m["user_id"] == user_id and m not in user_entries[-self.max_per_user:])
            ]

        logger.info(f"🧠 Memory updated for user: {user_id} → {entry['id']}")

    def recall(self, user_id: str) -> List[str]:
        entries = sorted(
            [m for m in self.memory if m["user_id"] == user_id],
            key=lambda x: x["timestamp"]
        )
        logger.info(f"🔁 Memory recall for user: {user_id} → {len(entries)} entries")
        return [m["text"] for m in entries]

    def clear(self, user_id: str) -> None:
        before = len(self.memory)
        self.memory = [m for m in self.memory if m["user_id"] != user_id]
        after = len(self.memory)
        logger.info(f"🗑️ Memory cleared for user: {user_id} ({before - after} removed)")
