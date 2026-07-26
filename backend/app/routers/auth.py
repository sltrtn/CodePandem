from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models_db import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=6, max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return AuthResponse(token=token, user=user.to_dict())


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    from datetime import datetime, timezone

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(user.id)
    return AuthResponse(token=token, user=user.to_dict())


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return user.to_dict()


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.elo.desc()).limit(limit).all()
    return [u.to_dict() for u in users]


@router.get("/users/{user_id}")
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


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
