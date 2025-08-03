# app/utils/redis_client.py

import logging
from typing import Optional

from redis import Redis

from app.config import config

# Initialize Redis client
try:
    tmp_client = Redis.from_url(config.REDIS_URL, decode_responses=True)
    tmp_client.ping()
    logging.getLogger("echoscript").info(f"Connected to Redis at {config.REDIS_URL}")
    redis_client: Optional[Redis] = tmp_client
except Exception as e:
    redis_client = None
    logging.getLogger("echoscript").warning(
        f"Could not connect to Redis at {config.REDIS_URL}: {e}"
    )


def get_redis() -> Redis:
    """
    Retrieve the Redis client instance. Raises RuntimeError if not connected.
    """
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized or connection failed.")
    return redis_client


# Convenience functions for common operations


def set_value(key: str, value: str, ex: Optional[int] = None) -> bool:
    """
    Set a key to a value with optional expiration (in seconds).
    Returns True if set succeeded, False otherwise.
    """
    client = get_redis()
    result = client.set(name=key, value=value, ex=ex)
    return result if result is not None else False


def get_value(key: str) -> Optional[str]:
    """
    Get a value by key. Returns None if key does not exist.
    """
    client = get_redis()
    return client.get(name=key)


def delete_key(key: str) -> int:
    """
    Delete a key. Returns the number of keys removed (0 or 1).
    """
    client = get_redis()
    return client.delete(key)


def exists(key: str) -> bool:
    """
    Check if a key exists. Returns True if it exists, False otherwise.
    """
    client = get_redis()
    return client.exists(key) == 1
