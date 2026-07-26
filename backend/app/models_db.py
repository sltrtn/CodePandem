from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _gen_id(n: int = 12) -> str:
    return uuid.uuid4().hex[:n]


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: _gen_id(12))
    username = Column(String(30), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    elo = Column(Float, default=1000.0, nullable=False)
    wins = Column(Integer, default=0, nullable=False)
    losses = Column(Integer, default=0, nullable=False)
    draws = Column(Integer, default=0, nullable=False)
    tier = Column(String(20), default="bronze", nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    last_login = Column(DateTime, default=_utcnow, nullable=False)

    matches = relationship(
        "MatchRecord",
        primaryjoin="User.id == MatchRecord.player1_id",
        foreign_keys="MatchRecord.player1_id",
        back_populates="user",
        lazy="dynamic",
    )

    def update_tier(self):
        if self.elo >= 2400:
            self.tier = "diamond"
        elif self.elo >= 2000:
            self.tier = "platinum"
        elif self.elo >= 1600:
            self.tier = "gold"
        elif self.elo >= 1200:
            self.tier = "silver"
        else:
            self.tier = "bronze"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "elo": round(self.elo, 1),
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "games_played": self.wins + self.losses + self.draws,
            "tier": self.tier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class MatchRecord(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, default=lambda: _gen_id(12))
    player1_id = Column(String, ForeignKey("users.id"), nullable=False)
    player2_id = Column(String, ForeignKey("users.id"), nullable=False)
    winner_id = Column(String, nullable=True)
    player1_elo_change = Column(Float, default=0.0, nullable=False)
    player2_elo_change = Column(Float, default=0.0, nullable=False)
    rounds_played = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="completed", nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    user = relationship(
        "User",
        foreign_keys=[player1_id],
        primaryjoin="MatchRecord.player1_id == User.id",
        back_populates="matches",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "winner_id": self.winner_id,
            "player1_elo_change": round(self.player1_elo_change, 1),
            "player2_elo_change": round(self.player2_elo_change, 1),
            "rounds_played": self.rounds_played,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
