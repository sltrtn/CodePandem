from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import (
    check_rate_limit,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    record_login_attempt,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
    validate_password,
    verify_password,
)
from app.database import get_db
from app.models_db import PasswordResetToken, RefreshToken, User
from app.seasons import create_season_stats_for_user

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class PasswordResetRequest(BaseModel):
    username: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=100)


class DeleteAccountRequest(BaseModel):
    password: str


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    valid, msg = validate_password(body.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    create_season_stats_for_user(db, user)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id, db)
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, user=user.to_dict()
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    identifier = body.username.lower()
    allowed, seconds = check_rate_limit(identifier)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Try again in {seconds}s.",
        )

    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        record_login_attempt(identifier, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    record_login_attempt(identifier, success=True)

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    create_season_stats_for_user(db, user)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id, db)
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, user=user.to_dict()
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    result = rotate_refresh_token(body.refresh_token, db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    access_token, refresh_token = result
    user_id = decode_token(access_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, user=user.to_dict()
    )


@router.post("/logout")
def logout(
    body: RefreshRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    revoke_refresh_token(body.refresh_token, db)
    return {"status": "logged_out"}


@router.post("/logout-all")
def logout_all(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    revoke_all_user_refresh_tokens(user.id, db)
    return {"status": "all_sessions_revoked"}


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    valid, msg = validate_password(body.new_password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    user.password_hash = hash_password(body.new_password)
    db.commit()

    # Revoke all other sessions for safety
    revoke_all_user_refresh_tokens(user.id, db)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id, db)
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, user=user.to_dict()
    )


@router.post("/password-reset-request")
def request_password_reset(body: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user:
        # Don't reveal whether user exists
        return {"status": "reset_requested"}

    # Invalidate old tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": datetime.now(timezone.utc)})

    token_value = secrets.token_urlsafe(32)
    prt = PasswordResetToken(
        token=token_value,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(prt)
    db.commit()

    # In production, send email here. For now, return token in dev mode.
    return {"status": "reset_requested", "token": token_value}


@router.post("/password-reset")
def confirm_password_reset(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    prt = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == body.token,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not prt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    valid, msg = validate_password(body.new_password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    user = db.query(User).filter(User.id == prt.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(body.new_password)
    prt.used_at = datetime.now(timezone.utc)
    db.commit()

    revoke_all_user_refresh_tokens(user.id, db)

    return {"status": "password_reset"}


@router.delete("/me")
def delete_account(
    request: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    db.delete(user)
    db.commit()
    return {"status": "account_deleted"}


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return user.to_dict()


@router.get("/leaderboard")
def get_leaderboard(
    season: str = "current",
    limit: int = 50,
    db: Session = Depends(get_db),
):
    if season == "alltime":
        users = db.query(User).order_by(User.elo.desc()).limit(limit).all()
        return [u.to_dict() for u in users]

    from app.models_db import UserSeasonStats
    from app.seasons import get_current_season

    current = get_current_season(db)
    stats = (
        db.query(UserSeasonStats)
        .filter(UserSeasonStats.season_id == current.id)
        .order_by(UserSeasonStats.season_elo.desc())
        .limit(limit)
        .all()
    )

    result = []
    for s in stats:
        user = db.query(User).filter(User.id == s.user_id).first()
        if user:
            result.append({
                "id": user.id,
                "username": user.username,
                "elo": round(s.season_elo, 1),
                "highest_elo": round(s.highest_season_elo, 1),
                "wins": s.wins,
                "losses": s.losses,
                "draws": s.draws,
                "games_played": s.games_played,
                "tier": user.tier,
            })
    return result


@router.get("/users/{user_id}")
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data = user.to_dict()
    from app.seasons import get_season_stats

    season_stats = get_season_stats(db, user_id)
    if season_stats:
        data["season"] = season_stats
    return data


@router.get("/users/{user_id}/matches")
def get_user_matches(user_id: str, limit: int = 20, db: Session = Depends(get_db)):
    from app.models_db import MatchRecord

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    matches = (
        db.query(MatchRecord)
        .filter((MatchRecord.player1_id == user_id) | (MatchRecord.player2_id == user_id))
        .order_by(MatchRecord.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for m in matches:
        p1 = db.query(User).filter(User.id == m.player1_id).first()
        p2 = db.query(User).filter(User.id == m.player2_id).first()
        results.append({
            **m.to_dict(),
            "player1_username": p1.username if p1 else m.player1_id,
            "player2_username": p2.username if p2 else m.player2_id,
        })
    return results


@router.get("/users/by-username/{username}")
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


@router.get("/users/search/{query}")
def search_users(query: str, limit: int = 10, db: Session = Depends(get_db)):
    users = (
        db.query(User)
        .filter(User.username.ilike(f"%{query}%"))
        .order_by(User.elo.desc())
        .limit(limit)
        .all()
    )
    return [u.to_dict() for u in users]
