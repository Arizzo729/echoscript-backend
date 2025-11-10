from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import config

from passlib.context import CryptContext


# Password hashing utilities

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_BCRYPT_BYTES = 72


def _truncate_password(password: str) -> str:
    """Truncate password safely to bcrypt's 72-byte limit."""
    if not password:
        return ""
    # Encode to bytes, truncate to 72 bytes max, decode back to string
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > MAX_BCRYPT_BYTES:
        pw_bytes = pw_bytes[:MAX_BCRYPT_BYTES]
        # Ensure we don't cut in the middle of a multi-byte character
        try:
            return pw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # If we cut mid-character, trim until valid
            for i in range(MAX_BCRYPT_BYTES, 0, -1):
                try:
                    return pw_bytes[:i].decode("utf-8")
                except UnicodeDecodeError:
                    continue
            return ""
    return password


def hash_password(password: str) -> str:
    """Hash password with automatic truncation."""
    safe_pw = _truncate_password(password)
    return pwd_context.hash(safe_pw)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password safely (also truncated)."""
    safe_pw = _truncate_password(plain_password)
    return pwd_context.verify(safe_pw, hashed_password)


# JWT token utilities


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """
    Create a signed JWT access token containing the provided data payload and expiration.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=6))
    to_encode.update({"exp": expire})

    token = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT access token. Returns the payload if valid, otherwise None.
    """
    try:
        payload = jwt.decode(
            token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None

