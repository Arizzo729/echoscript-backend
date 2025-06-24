# app/auth_utils.py

import bcrypt
import secrets
import hashlib
from datetime import datetime, timedelta
import jwt
import os
from typing import Optional

# === Environment Config ===
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")  # Change in production!
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24  # 24 hours

# === Password Hashing ===
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)  # Use 12 or higher in production
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# === Token Utilities ===
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRATION_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# === Secure Token Generation (e.g. for email validation, password reset) ===
def generate_secure_token(length: int = 64) -> str:
    return secrets.token_urlsafe(length)

# === SHA256 Fingerprinting (for optional client/session/device keys) ===
def sha256_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()
