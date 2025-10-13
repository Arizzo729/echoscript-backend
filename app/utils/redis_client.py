"""
Central place to get a Redis-like cache.

- If REDIS_ENABLED=false or REDIS_URL is missing/unreachable, we fall back to an
  in-memory dict with TTL so local dev keeps working.
- We do not connect at import time; first use will try once.
"""

from __future__ import annotations
import logging, time, threading
from typing import Any, Optional

from app.config import get_settings

log = logging.getLogger(__name__)

_redis_client = None
_redis_checked = False
_lock = threading.Lock()


def _connect_redis():
    global _redis_client, _redis_checked
    with _lock:
        if _redis_checked:
            return _redis_client
        _redis_checked = True

        settings = get_settings()
        if not settings.REDIS_ENABLED:
            log.info("Redis disabled via REDIS_ENABLED=false")
            _redis_client = None
            return None

        url = settings.REDIS_URL
        if not url:
            log.info("REDIS_URL not set; using in-memory cache fallback")
            _redis_client = None
            return None

        try:
            import redis  # pip install redis
            client = redis.from_url(url, decode_responses=True, socket_timeout=2)
            # Optional: a light liveness check (won't run until first use)
            client.ping()
            log.info("Connected to Redis at %s", url.split("@")[-1])
            _redis_client = client
            return client
        except Exception as e:
            log.warning("Redis unavailable (%s). Using in-memory cache.", e)
            _redis_client = None
            return None


# -------- In-memory fallback with TTL --------

class _MemoryCache:
    def __init__(self):
        self._store: dict[str, tuple[Any, Optional[float]]] = {}
        self._lock = threading.Lock()

    def _expired(self, key: str) -> bool:
        item = self._store.get(key)
        if not item:
            return True
        _, exp = item
        return exp is not None and exp < time.time()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            if self._expired(key):
                self._store.pop(key, None)
                return None
            val, _ = self._store[key]
            return val

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        with self._lock:
            if not isinstance(value, (str, bytes, int, float)):
                import json
                value = json.dumps(value)
            exp_ts = time.time() + ex if ex else None
            self._store[key] = (value, exp_ts)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    # common aliases
    def setex(self, key: str, ex: int, value: Any) -> None:
        self.set(key, value, ex=ex)

    def expire(self, key: str, ex: int) -> None:
        with self._lock:
            if key in self._store:
                val, _ = self._store[key]
                self._store[key] = (val, time.time() + ex)

    def ping(self) -> bool:
        return True


_memory_cache = _MemoryCache()


class Cache:
    """Facade that exposes a subset of redis-py API against Redis or memory."""

    @property
    def _client(self):
        return _connect_redis()

    def get(self, key: str) -> Optional[str]:
        client = self._client
        if client is None:
            return _memory_cache.get(key)
        return client.get(key)

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        client = self._client
        if client is None:
            _memory_cache.set(key, value, ex=ex)
            return
        if ex is None:
            client.set(key, value)
        else:
            client.setex(key, ex, value)

    def delete(self, key: str) -> None:
        client = self._client
        if client is None:
            _memory_cache.delete(key)
            return
        client.delete(key)

    def expire(self, key: str, ex: int) -> None:
        client = self._client
        if client is None:
            _memory_cache.expire(key, ex)
            return
        client.expire(key, ex)

    def ping(self) -> bool:
        client = self._client
        if client is None:
            return _memory_cache.ping()
        return bool(client.ping())


# A ready-to-import singleton
cache = Cache()

