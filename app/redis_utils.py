# app/redis_utils.py

import redis
import os
import logging

logger = logging.getLogger("echoscript")

# === Redis Client Loader ===
def get_redis_client():
    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        logger.warning("[Redis ⚠️ ] REDIS_URL not set in environment.")
        return None

    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        logger.info("[Redis ✅ ] Connection established successfully.")
        return client
    except redis.RedisError as e:
        logger.warning(f"[Redis ⚠️ ] Connection failed: {e}")
        return None

# === Global Redis Client Instance ===
redis_client = get_redis_client()
