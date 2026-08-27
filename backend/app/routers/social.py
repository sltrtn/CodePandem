from __future__ import annotations

import random
import string
from datetime import datetime, timezone

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import CONFIG
from app.database import get_db
from app.lobby import lobby
from app.matchmaking import matchmaker
from app.models import Match, PlayerRoundState, PlayerState, Round
from app.models_db import Friendship, User
from app.problems import get_problems_for_match
from app.ws.challenge import notify_user_challenge

router = APIRouter(prefix="/social", tags=["social"])

_custom_lobbies: dict[str, dict] = {}

# ── Friends ────────────────────────────────────────


@router.post("/friends/request/{user_id}")
def send_friend_request(
    user_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(404, "User not found")
    if user_id == user.id:
        raise HTTPException(400, "Cannot friend yourself")

    existing = (
        db.query(Friendship)
        .filter(
            ((Friendship.requester_id == user.id) & (Friendship.addressee_id == user_id))
            | ((Friendship.requester_id == user_id) & (Friendship.addressee_id == user.id))
        )
        .first()
    )
    if existing:
        if existing.status == "accepted":
            raise HTTPException(409, "Already friends")
        if existing.status == "pending":
            if existing.addressee_id == user.id:
                existing.status = "accepted"
                existing.updated_at = datetime.now(timezone.utc)
                db.commit()
                return {"status": "friend_request_accepted"}
            raise HTTPException(409, "Friend request already sent")
        raise HTTPException(409, "Friend request already exists")

    f = Friendship(requester_id=user.id, addressee_id=user_id)
    db.add(f)
    db.commit()
    return {"status": "friend_request_sent"}


@router.post("/friends/accept/{user_id}")
def accept_friend_request(
    user_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    f = (
        db.query(Friendship)
        .filter(
            Friendship.requester_id == user_id,
            Friendship.addressee_id == user.id,
            Friendship.status == "pending",
        )
        .first()
    )
    if not f:
        raise HTTPException(404, "No pending request from this user")
    f.status = "accepted"
    db.commit()
    return {"status": "friend_request_accepted"}


@router.post("/friends/decline/{user_id}")
def decline_friend_request(
    user_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    f = (
        db.query(Friendship)
        .filter(
            Friendship.requester_id == user_id,
            Friendship.addressee_id == user.id,
            Friendship.status == "pending",
        )
        .first()
    )
    if not f:
        raise HTTPException(404, "No pending request from this user")
    f.status = "declined"
    db.commit()
    return {"status": "friend_request_declined"}


@router.post("/friends/remove/{user_id}")
def remove_friend(
    user_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    f = (
        db.query(Friendship)
        .filter(
            ((Friendship.requester_id == user.id) & (Friendship.addressee_id == user_id))
            | ((Friendship.requester_id == user_id) & (Friendship.addressee_id == user.id)),
            Friendship.status == "accepted",
        )
        .first()
    )
    if not f:
        raise HTTPException(404, "Friendship not found")
    db.delete(f)
    db.commit()
    return {"status": "friend_removed"}


@router.get("/friends")
def list_friends(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sent = (
        db.query(Friendship)
        .filter(Friendship.requester_id == user.id, Friendship.status == "accepted")
        .all()
    )
    received = (
        db.query(Friendship)
        .filter(Friendship.addressee_id == user.id, Friendship.status == "accepted")
        .all()
    )

    friends = []
    for f in sent:
        u = db.query(User).filter(User.id == f.addressee_id).first()
        if u:
            online = lobby.get_player(u.id)
            friends.append({
                "user_id": u.id,
                "username": u.username,
                "elo": round(u.elo, 1),
                "tier": u.tier,
                "online": online is not None,
                "status": online.status if online else "offline",
            })
    for f in received:
        u = db.query(User).filter(User.id == f.requester_id).first()
        if u:
            online = lobby.get_player(u.id)
            friends.append({
                "user_id": u.id,
                "username": u.username,
                "elo": round(u.elo, 1),
                "tier": u.tier,
                "online": online is not None,
                "status": online.status if online else "offline",
            })

    return friends


@router.get("/friends/requests")
def list_friend_requests(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    incoming = (
        db.query(Friendship)
        .filter(Friendship.addressee_id == user.id, Friendship.status == "pending")
        .all()
    )
    result = []
    for f in incoming:
        u = db.query(User).filter(User.id == f.requester_id).first()
        if u:
            result.append({
                "user_id": u.id,
                "username": u.username,
                "elo": round(u.elo, 1),
                "tier": u.tier,
            })
    return result


# ── Custom Lobbies ─────────────────────────────────


@router.post("/lobby/create")
def create_custom_lobby(
    user: User = Depends(get_current_user),
):
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    _custom_lobbies[code] = {
        "host_id": user.id,
        "host_username": user.username,
        "players": [user.id],
        "status": "waiting",
    }
    return {"code": code, "status": "lobby_created"}


@router.post("/lobby/join/{code}")
def join_custom_lobby(
    code: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lobby_data = _custom_lobbies.get(code)
    if not lobby_data:
        raise HTTPException(404, "Lobby not found")
    if lobby_data["status"] != "waiting":
        raise HTTPException(400, "Lobby already started")
    if len(lobby_data["players"]) >= 2:
        raise HTTPException(400, "Lobby is full")
    if user.id in lobby_data["players"]:
        raise HTTPException(400, "Already in this lobby")

    lobby_data["players"].append(user.id)
    lobby_data["status"] = "starting"

    p1 = lobby.get_player(lobby_data["host_id"])
    p2 = lobby.get_player(user.id)
    if not p1 or not p2:
        lobby_data["status"] = "waiting"
        lobby_data["players"].remove(user.id)
        raise HTTPException(400, "Host is offline")

    match = Match()
    match.players[lobby_data["host_id"]] = PlayerState(
        player_id=lobby_data["host_id"], ws=p1.ws
    )
    match.players[user.id] = PlayerState(player_id=user.id, ws=p2.ws)
    match._usernames = {
        lobby_data["host_id"]: lobby_data["host_username"],
        user.id: user.username,
    }
    match.mode = "unranked"
    matchmaker._matches[match.match_id] = match
    matchmaker._player_match[lobby_data["host_id"]] = match.match_id
    matchmaker._player_match[user.id] = match.match_id

    lobby.set_status(lobby_data["host_id"], "in_match", match.match_id)
    lobby.set_status(user.id, "in_match", match.match_id)
    asyncio.create_task(lobby.broadcast({
        "type": "player_status_changed",
        "player_id": lobby_data["host_id"],
        "status": "in_match",
        "match_id": match.match_id,
        "online_count": lobby.online_count,
    }))
    asyncio.create_task(lobby.broadcast({
        "type": "player_status_changed",
        "player_id": user.id,
        "status": "in_match",
        "match_id": match.match_id,
        "online_count": lobby.online_count,
    }))

    problems = get_problems_for_match()
    for i, problem in enumerate(problems):
        time_limit = CONFIG.ROUND_TIMES[i]
        rnd = Round(
            round_number=i + 1,
            problem=problem,
            time_limit_s=time_limit,
            status="active" if i == 0 else "pending",
            players={
                lobby_data["host_id"]: PlayerRoundState(player_id=lobby_data["host_id"]),
                user.id: PlayerRoundState(player_id=user.id),
            },
        )
        match.rounds.append(rnd)

    match.current_round = 1
    match.status = "round_active"

    _custom_lobbies.pop(code, None)

    asyncio.create_task(notify_user_challenge(lobby_data["host_id"], {
        "type": "custom_lobby_started",
        "match_id": match.match_id,
        "opponent": user.username,
    }))

    return {
        "status": "lobby_joined",
        "match_id": match.match_id,
        "opponent": lobby_data["host_username"],
    }
