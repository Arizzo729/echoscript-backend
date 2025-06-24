import bcrypt
import secrets
import hashlib
from datetime import datetime, timedelta
import jwt
import os
from typing import Optional

# === Environment Config ===
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")  # Replace in production
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", 60 * 24))  # 24 hours default

# === Password Hashing ===
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

# === Token Creation ===
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRATION_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# === Secure Random Token (e.g. email validation, password reset) ===
def generate_secure_token(length: int = 64) -> str:
    return secrets.token_urlsafe(length)

# === Optional SHA256 Fingerprint for sessions/devices ===
def sha256_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
