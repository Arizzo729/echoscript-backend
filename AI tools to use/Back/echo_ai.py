# app/utils/echo_ai.py

import hashlib
import json
import logging
import zlib
from typing import Any, Optional

import openai
from openai import OpenAIError

from app.config import config
from app.utils.redis_client import redis_client  # type: ignore[attr-defined]

# Alias ChatCompletion so MyPy recognizes it
ChatCompletion: Any = openai.ChatCompletion  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)

# Ensure OpenAI key is set once
openai.api_key = config.OPENAI_API_KEY


def get_text_checksum(text: str) -> str:
    """
    Compute a SHA-256 checksum of the compressed text.
    Uses zlib.compress to normalize input, then hashlib.sha256 for strength.
    """
    compressed = zlib.compress(text.encode("utf-8"))
    # sha256 is cryptographically strong and avoids Bandit B324 warnings
    return hashlib.sha256(compressed).hexdigest()


def fetch_cached_response(key: str) -> Optional[str]:
    """
    Retrieve a cached AI response from Redis.
    Returns None on any error or if no cache entry exists.
    """
    if redis_client is None:
        return None
    try:
        raw = redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Redis GET failed for key={key}: {e}")
        return None


def cache_response(key: str, value: str, ttl: int = 3600) -> None:
    """
    Cache a JSON‑serializable AI response in Redis with a TTL (in seconds).
    Logs but ignores any Redis errors.
    """
    if redis_client is None:
        return
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.warning(f"Redis SETEX failed for key={key}: {e}")


def call_openai_chat(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 500,
    cache: bool = True,
    cache_ttl: int = 3600,
) -> str:
    """
    Send a ChatCompletion request to OpenAI, optionally caching the response.

    - system_prompt: the system-level instruction
    - user_prompt: the actual user content
    - cache: whether to read/write Redis cache
    - cache_ttl: time-to-live for cache in seconds
    """
    # Build a cache key from the combined prompt checksum
    checksum = get_text_checksum(system_prompt + user_prompt)
    cache_key = f"ai_resp:{checksum}"

    # Try returning the cached response
    if cache:
        cached = fetch_cached_response(cache_key)
        if cached is not None:
            logger.debug(f"Cache HIT for key={cache_key}")
            return cached
        logger.debug(f"Cache MISS for key={cache_key}")

    # No cache or miss — call OpenAI
    try:
        response = ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content.strip()
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error calling OpenAI: {e}")
        raise

    # Cache and return
    if cache:
        cache_response(cache_key, text, ttl=cache_ttl)
    return text
