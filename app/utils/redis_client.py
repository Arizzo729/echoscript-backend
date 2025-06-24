# ---- EchoScript.AI: utils/redis_client.py ----

import redis
from redis.exceptions import RedisError, ConnectionError
from app.config import Config
from app.utils.logger import logger

class RedisClient:
    def __init__(self, url: str = None):
        self.url = url or Config.REDIS_URL
        try:
            self.client = redis.Redis.from_url(self.url, decode_responses=True)
            self.client.ping()
            logger.info("✅ Connected to Redis")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.client = None

    # ---- Basic Key/Value Operations ----
    def set(self, key: str, value: str, ex: int = None):
        try:
            return self.client.set(key, value, ex=ex)
        except RedisError as e:
            logger.error(f"Redis SET error: {e}")
            return None

    def get(self, key: str):
        try:
            return self.client.get(key)
        except RedisError as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def delete(self, key: str):
        try:
            return self.client.delete(key)
        except RedisError as e:
            logger.error(f"Redis DELETE error: {e}")
            return 0

    def exists(self, key: str) -> bool:
        try:
            return self.client.exists(key) == 1
        except RedisError as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    def incr(self, key: str):
        try:
            return self.client.incr(key)
        except RedisError as e:
            logger.error(f"Redis INCR error: {e}")
            return None

    def setex(self, key: str, time, value: str):
        try:
            return self.client.setex(key, time, value)
        except RedisError as e:
            logger.error(f"Redis SETEX error: {e}")
            return None

    def keys(self, pattern: str):
        try:
            return self.client.keys(pattern)
        except RedisError as e:
            logger.error(f"Redis KEYS error: {e}")
            return []

    # ---- Hash Operations ----
    def hset(self, name: str, key: str, value: str):
        try:
            return self.client.hset(name, key, value)
        except RedisError as e:
            logger.error(f"Redis HSET error: {e}")
            return None

    def hget(self, name: str, key: str):
        try:
            return self.client.hget(name, key)
        except RedisError as e:
            logger.error(f"Redis HGET error: {e}")
            return None

    def hgetall(self, name: str):
        try:
            return self.client.hgetall(name)
        except RedisError as e:
            logger.error(f"Redis HGETALL error: {e}")
            return {}

    # ---- Flush All (use cautiously) ----
    def flush(self):
        try:
            return self.client.flushall()
        except RedisError as e:
            logger.error(f"Redis FLUSH error: {e}")
            return None

# ✅ Singleton redis_client available app-wide
redis_client = RedisClient()

