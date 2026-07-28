from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models_db import Season, User
from app.seasons import create_new_season, get_current_season, get_season_stats

router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.get("/current")
def current_season(db: Session = Depends(get_db)):
    season = get_current_season(db)
    return season.to_dict()


@router.get("/")
def list_seasons(db: Session = Depends(get_db)):
    seasons = db.query(Season).order_by(Season.created_at.desc()).all()
    return [s.to_dict() for s in seasons]


@router.get("/stats")
def my_season_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stats = get_season_stats(db, user.id)
    if not stats:
        raise HTTPException(404, "No season stats found")
    return stats


@router.get("/stats/{user_id}")
def user_season_stats(
    user_id: str,
    db: Session = Depends(get_db),
):
    stats = get_season_stats(db, user_id)
    if not stats:
        raise HTTPException(404, "No season stats found")
    return stats


@router.post("/admin/new")
def admin_new_season(name: str | None = None):
    season = create_new_season(name)
    return season.to_dict()
