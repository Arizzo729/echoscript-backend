# app/utils/safety_check.py

import os
from app.config import Config, redis_client
from app.utils.logger import logger

def run_safety_checks():
    # === Env Vars ===
    required_env_vars = ["OPENAI_API_KEY", "JWT_SECRET_KEY", "REDIS_URL", "DATABASE_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.critical(f"[❌ CONFIG] Missing required environment variables: {missing_vars}")
        raise SystemExit("Startup halted. Required environment variables not set.")

    # === Redis Connection ===
    try:
        if not redis_client.client or not redis_client.client.ping():
            logger.critical("[❌ REDIS] Connection to Redis failed. Check REDIS_URL and service status.")
            raise SystemExit("Startup halted. Redis unavailable.")
    except Exception as e:
        logger.critical(f"[❌ REDIS] Redis check failed: {e}")
        raise SystemExit("Startup halted. Redis check error.")

    logger.info("[✅ SAFETY] All core systems passed initial checks.")
