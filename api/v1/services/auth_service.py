import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import jwt


# Configuration (can be overridden with environment variables)
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))


def create_access_token(subject: Any, extra_claims: Optional[dict] = None) -> str:
    """Create a JWT access token for a subject (usually user id).

    The token contains `sub` and an expiry (`exp`).
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # PyJWT returns str for modern versions
    return token


def generate_refresh_token(subject: Any | None = None, extra_claims: Optional[dict] = None) -> str:
    """Generate a signed JWT refresh token.

    The token will include:
    - `sub`: optional subject (usually user id)
    - `jti`: unique id for the token
    - `iat` / `exp`: issued-at and expiry
    - `type`: "refresh"

    Returns a JWT string.
    """
    now = datetime.now(timezone.utc)
    jti = uuid.uuid4().hex
    payload = {
        "jti": jti,
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }

    if subject is not None:
        payload["sub"] = str(subject)

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
