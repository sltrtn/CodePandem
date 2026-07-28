from __future__ import annotations

import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models_db import RefreshToken, User

SECRET_KEY = os.getenv("CODEPANDEM_JWT_SECRET", "codepandem-dev-secret-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()

# ── Password hashing ───────────────────────────────


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Password validation ────────────────────────────


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain an uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain a lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain a number"
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        return False, "Password must contain a special character"
    return True, ""


# ── Token creation / decode ────────────────────────


def _create_jwt_token(user_id: str, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(
        {"sub": user_id, "type": token_type, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_access_token(user_id: str) -> str:
    return _create_jwt_token(
        user_id, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(user_id: str, db: Session) -> str:
    token_value = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(
        token=token_value,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(rt)
    db.commit()
    return token_value


def decode_token(token: str, expected_type: str = "access") -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload.get("sub")
    except JWTError:
        return None


# ── Current user resolution ────────────────────────


def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_token(cred.credentials, expected_type="access")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


def get_current_user_optional(
    cred: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    user_id = decode_token(cred.credentials, expected_type="access")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def authenticate_ws_token(token: str, db: Session) -> User | None:
    user_id = decode_token(token, expected_type="access")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


# ── Refresh token rotation ─────────────────────────


def rotate_refresh_token(refresh_token: str, db: Session) -> tuple[str, str] | None:
    now = datetime.now(timezone.utc)
    rt = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .first()
    )
    if not rt:
        return None

    # Revoke old token
    rt.revoked_at = now

    # Create new tokens
    user_id = rt.user_id
    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id, db)
    db.commit()
    return new_access, new_refresh


def revoke_refresh_token(refresh_token: str, db: Session) -> None:
    rt = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if rt:
        rt.revoked_at = datetime.now(timezone.utc)
        db.commit()


def revoke_all_user_refresh_tokens(user_id: str, db: Session) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": datetime.now(timezone.utc)})
    db.commit()


# ── Rate limiting ──────────────────────────────────

_login_attempts: dict[str, list[datetime]] = {}
_login_lockouts: dict[str, datetime] = {}


def _cleanup_attempts(identifier: str) -> None:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=15)
    attempts = _login_attempts.get(identifier, [])
    _login_attempts[identifier] = [a for a in attempts if a > cutoff]


def check_rate_limit(identifier: str) -> tuple[bool, int]:
    """Returns (allowed, seconds_remaining)."""
    now = datetime.now(timezone.utc)

    # Check lockout
    lockout_until = _login_lockouts.get(identifier)
    if lockout_until and lockout_until > now:
        return False, int((lockout_until - now).total_seconds())
    elif lockout_until and lockout_until <= now:
        _login_lockouts.pop(identifier, None)

    _cleanup_attempts(identifier)
    attempts = _login_attempts.get(identifier, [])

    # 5 attempts per 15 minutes
    if len(attempts) >= 5:
        lockout_until = now + timedelta(minutes=15)
        _login_lockouts[identifier] = lockout_until
        return False, int((lockout_until - now).total_seconds())

    return True, 0


def record_login_attempt(identifier: str, success: bool) -> None:
    now = datetime.now(timezone.utc)
    if success:
        _login_attempts.pop(identifier, None)
        _login_lockouts.pop(identifier, None)
        return

    _cleanup_attempts(identifier)
    _login_attempts.setdefault(identifier, []).append(now)
