import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    """Hash a one-time login code with a keyed sha256.

    Login codes are short-lived (5 min), per-challenge, and rate-limited, so a
    fast keyed hash is sufficient. Real durable passwords are NOT used by this
    platform per FDD A04.
    """
    key = settings.JWT_SECRET_KEY.encode("utf-8")
    return hmac.new(key, plain.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(plain), hashed)


def generate_random_password(length: int = 8) -> str:
    """Numeric one-time login code."""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_api_key_secret(secret: str) -> str:
    """Deterministic hash so we can look up keys by hash on the gateway hot path."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def generate_api_key_secret() -> tuple[str, str, str]:
    """Return (raw_secret, prefix, mask)."""
    raw = "sk-" + secrets.token_urlsafe(32).replace("_", "").replace("-", "")[:40]
    prefix = raw[:6]
    mask = f"{raw[:6]}...{raw[-4:]}"
    return raw, prefix, mask


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def encode_access_token(user_id: str, role_id: str, permissions: list[str]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role_id": role_id,
        "permissions": permissions,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def encode_refresh_token(user_id: str, session_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "sid": session_id,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Coerce a datetime to a tz-aware UTC datetime.

    SQLAlchemy + Postgres returns tz-aware datetimes from `DateTime(timezone=True)`,
    but SQLite/aiosqlite returns naive ones. We treat naive as UTC.
    """
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
