# app/utils/redis_client.py
from __future__ import annotations

import logging
from typing import Any, Optional

from redis import ConnectionError as RedisConnectionError
from redis import Redis

from app.core.settings import settings

logger = logging.getLogger("echoscript")

# A single, cached Redis client instance
_redis_client: Optional[Redis] = None

def get_redis() -> Redis:
    """
    Returns a Redis client instance.

    If the connection fails or is disabled, it will not raise an exception
    but will return a dummy client that does nothing.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    if settings.DISABLE_REDIS:
        logger.warning("Redis is disabled. Using a non-functional dummy client.")
        _redis_client = _MemoryRedis() # type: ignore
        return _redis_client # type: ignore

    try:
        logger.info(f"Connecting to Redis at {settings.REDIS_URL}")
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        _redis_client = client
        logger.info("Connected to Redis successfully.")
    except (RedisConnectionError, OSError) as e:
        logger.warning(f"Redis unavailable, using in-memory shim. Reason: {e}")
        _redis_client = _MemoryRedis() # type: ignore
    except Exception as e:
        logger.error(f"Unexpected Redis error '{e}', using in-memory shim.")
        _redis_client = _MemoryRedis() # type: ignore
    
    return _redis_client # type: ignore

class _MemoryRedis:
    """A dummy client that mimics Redis for environments where Redis is not available."""
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        logger.warning("Using in-memory Redis shim. Data will not be persisted.")

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        self._store[key] = str(value)
        return True

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0

    def exists(self, key: str) -> int:
        return 1 if key in self._store else 0

    def ping(self) -> bool:
        return True

# Export a single instance for convenience in other modules
redis_client = get_redis()