"""Password hashing and JWT helpers."""
from datetime import datetime, timedelta, timezone
from fastapi import Header, HTTPException
from passlib.context import CryptContext
from jose import jwt

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except jwt.JWTError:
        return None


def require_amalgamator_key(x_amalgamator_key: str = Header(default=None)):
    """
    Gate for the read-only Amalgamator status-report endpoint - a completely
    separate shared-secret header, never a user login/JWT. See
    routers/amalgamator.py.
    """
    if not settings.amalgamator_api_key:
        raise HTTPException(status_code=503, detail="Amalgamator access is not configured on this app yet")
    if x_amalgamator_key != settings.amalgamator_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing Amalgamator API key")
    return True
