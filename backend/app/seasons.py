from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import CONFIG
from app.database import SessionLocal
from app.models_db import Season, User, UserSeasonStats


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_current_season(db: Session | None = None) -> Season:
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        season = db.query(Season).filter(Season.active == True).first()
        if season:
            return season

        # Auto-create first season
        now = _utcnow()
        count = db.query(Season).count()
        season = Season(
            name=f"Season {count + 1}",
            start_at=now,
            end_at=now + timedelta(days=CONFIG.SEASON_DURATION_DAYS),
            active=True,
        )
        db.add(season)
        db.commit()
        db.refresh(season)

        # Create season stats for all existing users
        _ensure_season_stats(db, season.id)

        return season
    finally:
        if close_db:
            db.close()


def get_current_season_id() -> str:
    return get_current_season().id


def _ensure_season_stats(db: Session, season_id: str) -> None:
    users = db.query(User).all()
    for user in users:
        existing = (
            db.query(UserSeasonStats)
            .filter(
                UserSeasonStats.user_id == user.id,
                UserSeasonStats.season_id == season_id,
            )
            .first()
        )
        if existing:
            continue

        reset_elo = (user.elo + CONFIG.SEASON_SOFT_RESET_BASE) / 2
        stats = UserSeasonStats(
            user_id=user.id,
            season_id=season_id,
            season_elo=reset_elo,
            highest_season_elo=reset_elo,
        )
        db.add(stats)
    db.commit()


def create_season_stats_for_user(db: Session, user: User) -> None:
    season = get_current_season(db)
    existing = (
        db.query(UserSeasonStats)
        .filter(
            UserSeasonStats.user_id == user.id,
            UserSeasonStats.season_id == season.id,
        )
        .first()
    )
    if existing:
        return

    reset_elo = (user.elo + CONFIG.SEASON_SOFT_RESET_BASE) / 2
    stats = UserSeasonStats(
        user_id=user.id,
        season_id=season.id,
        season_elo=reset_elo,
        highest_season_elo=reset_elo,
    )
    db.add(stats)
    db.commit()


def create_new_season(name: str | None = None) -> Season:
    db = SessionLocal()
    try:
        # Deactivate current season
        db.query(Season).filter(Season.active == True).update({"active": False})
        db.commit()

        now = _utcnow()
        count = db.query(Season).count()
        season = Season(
            name=name or f"Season {count + 1}",
            start_at=now,
            end_at=now + timedelta(days=CONFIG.SEASON_DURATION_DAYS),
            active=True,
        )
        db.add(season)
        db.commit()
        db.refresh(season)

        _ensure_season_stats(db, season.id)
        return season
    finally:
        db.close()


def get_season_stats(db: Session, user_id: str, season_id: str | None = None):
    if season_id is None:
        season = get_current_season(db)
        season_id = season.id

    stats = (
        db.query(UserSeasonStats)
        .filter(
            UserSeasonStats.user_id == user_id,
            UserSeasonStats.season_id == season_id,
        )
        .first()
    )
    if not stats:
        return None
    return stats.to_dict()
