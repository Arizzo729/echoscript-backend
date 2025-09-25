# app/utils/redis_client.py
from __future__ import annotations

import logging
from typing import Any, Optional

from redis import ConnectionError as RedisConnectionError
from redis import Redis

from app.config import config

logger = logging.getLogger("echoscript")


class _MemoryRedis:
    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        if isinstance(value, str):
            value = value.encode("utf-8")
        elif not isinstance(value, (bytes, bytearray)):
            value = str(value).encode("utf-8")
        self._store[key] = value
        return True

    def get(self, key: str) -> Optional[bytes]:
        return self._store.get(key)

    def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0

    def exists(self, key: str) -> int:
        return 1 if key in self._store else 0

    def ping(self) -> bool:
        return True


_cached_client: Optional[Redis | _MemoryRedis] = None


def _build_real_redis() -> Redis:
    url = config.REDIS_URL or "redis://localhost:6379/0"
    logger.info(f"Connecting to Redis at {url}")
    client = Redis.from_url(url, decode_responses=False)
    client.ping()
    return client


def get_redis() -> Redis | _MemoryRedis:
    global _cached_client
    if _cached_client is not None:
        return _cached_client
    try:
        _cached_client = _build_real_redis()
        logger.info("Connected to Redis successfully.")
    except (RedisConnectionError, OSError) as e:
        logger.warning(f"Redis unavailable, using in-memory shim. Reason: {e}")
        _cached_client = _MemoryRedis()
    except Exception as e:
        logger.error(f"Unexpected Redis error '{e}', using in-memory shim.")
        _cached_client = _MemoryRedis()
    return _cached_client


def set_value(key: str, value: Any, ex: Optional[int] = None) -> bool:
    try:
        return bool(get_redis().set(key, value, ex=ex))  # type: ignore[attr-defined]
    except Exception as e:
        logger.error(f"Redis set failed for {key}: {e}")
        return False


def get_value(key: str, as_text: bool = True) -> Optional[str | bytes]:
    try:
        raw = get_redis().get(key)  # type: ignore[attr-defined]
        if raw is None:
            return None
        if as_text:
            try:
                return raw.decode("utf-8")
            except Exception:
                return None
        return raw
    except Exception as e:
        logger.error(f"Redis get failed for {key}: {e}")
        return None


def delete_key(key: str) -> int:
    try:
        return int(get_redis().delete(key))  # type: ignore[attr-defined]
    except Exception as e:
        logger.error(f"Redis delete failed for {key}: {e}")
        return 0


def exists(key: str) -> bool:
    try:
        return int(get_redis().exists(key)) == 1  # type: ignore[attr-defined]
    except Exception as e:
        logger.error(f"Redis exists failed for {key}: {e}")
        return False


# legacy export
redis_client = get_redis()

__all__ = [
    "get_redis",
    "set_value",
    "get_value",
    "delete_key",
    "exists",
    "redis_client",
]
