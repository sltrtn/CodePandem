from __future__ import annotations

import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth import authenticate_ws_token
from app.config import CONFIG
from app.database import SessionLocal
from app.lobby import lobby
from app.matchmaking import matchmaker
from app.models import Match, PlayerRoundState, PlayerState, Round
from app.problems import get_problems_for_match
from app.seasons import get_current_season_id

router = APIRouter()

# user_id -> WebSocket
_challenge_ws: dict[str, WebSocket] = {}


async def notify_user_challenge(user_id: str, message: dict) -> None:
    """Send a message to a user's challenge WebSocket if connected."""
    ws = _challenge_ws.get(user_id)
    if not ws:
        return
    if ws.client_state.name != "CONNECTED":
        _challenge_ws.pop(user_id, None)
        return
    try:
        await ws.send_json(message)
    except Exception:
        _challenge_ws.pop(user_id, None)


@router.websocket("/ws/challenge")
async def ws_challenge(ws: WebSocket):
    await ws.accept()

    token = ws.query_params.get("token")
    if not token:
        await ws.send_json({"type": "error", "message": "Authentication required"})
        await ws.close()
        return

    db = SessionLocal()
    try:
        user = authenticate_ws_token(token, db)
        if not user:
            await ws.send_json({"type": "error", "message": "Invalid token"})
            await ws.close()
            return
        user_id = user.id
        username = user.username
    finally:
        db.close()

    _challenge_ws[user_id] = ws

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "challenge_player":
                target_id = data.get("target_id")
                if not target_id:
                    await ws.send_json({"type": "error", "message": "target_id required"})
                    continue

                target = lobby.get_player(target_id)
                if not target or target.status == "in_match":
                    await ws.send_json({"type": "error", "message": "User not available"})
                    continue

                challenge_id = uuid.uuid4().hex[:8]
                matchmaker.add_pending_challenge(
                    challenge_id, user_id, username, target_id
                )

                await ws.send_json({
                    "type": "challenge_sent",
                    "challenge_id": challenge_id,
                    "target_id": target_id,
                })

                # Notify target via challenge WS if connected, else lobby WS
                target_ws = _challenge_ws.get(target_id)
                if target_ws:
                    try:
                        await target_ws.send_json({
                            "type": "challenge_received",
                            "challenge_id": challenge_id,
                            "challenger_id": user_id,
                            "challenger_username": username,
                        })
                    except Exception:
                        pass
                elif target.ws:
                    try:
                        await target.ws.send_json({
                            "type": "challenge_received",
                            "challenge_id": challenge_id,
                            "challenger_id": user_id,
                            "challenger_username": username,
                        })
                    except Exception:
                        pass

            elif msg_type == "accept_challenge":
                challenge_id = data.get("challenge_id")
                chal = matchmaker.pop_pending_challenge(challenge_id)
                if not chal or chal["target_id"] != user_id:
                    await ws.send_json({"type": "error", "message": "Invalid challenge"})
                    continue

                chal["status"] = "accepted"
                p1 = lobby.get_player(chal["challenger_id"])
                p2 = lobby.get_player(chal["target_id"])
                if not p1 or not p2:
                    await ws.send_json({"type": "error", "message": "Player offline"})
                    continue

                match = Match()
                match.players[chal["challenger_id"]] = PlayerState(
                    player_id=chal["challenger_id"], ws=p1.ws
                )
                match.players[chal["target_id"]] = PlayerState(
                    player_id=chal["target_id"], ws=p2.ws
                )
                match._usernames = {
                    chal["challenger_id"]: chal["challenger_username"],
                    chal["target_id"]: username,
                }
                match.mode = "ranked"
                match.season_id = get_current_season_id()
                matchmaker._matches[match.match_id] = match
                matchmaker._player_match[chal["challenger_id"]] = match.match_id
                matchmaker._player_match[chal["target_id"]] = match.match_id

                lobby.set_status(chal["challenger_id"], "in_match", match.match_id)
                lobby.set_status(chal["target_id"], "in_match", match.match_id)
                await lobby.broadcast({
                    "type": "player_status_changed",
                    "player_id": chal["challenger_id"],
                    "status": "in_match",
                    "match_id": match.match_id,
                    "online_count": lobby.online_count,
                })
                await lobby.broadcast({
                    "type": "player_status_changed",
                    "player_id": chal["target_id"],
                    "status": "in_match",
                    "match_id": match.match_id,
                    "online_count": lobby.online_count,
                })

                problems = get_problems_for_match()
                for i, problem in enumerate(problems):
                    time_limit = CONFIG.ROUND_TIMES[i]
                    rnd = Round(
                        round_number=i + 1,
                        problem=problem,
                        time_limit_s=time_limit,
                        status="active" if i == 0 else "pending",
                        players={
                            chal["challenger_id"]: PlayerRoundState(player_id=chal["challenger_id"]),
                            chal["target_id"]: PlayerRoundState(player_id=chal["target_id"]),
                        },
                    )
                    match.rounds.append(rnd)

                match.current_round = 1
                match.status = "round_active"

                await ws.send_json({
                    "type": "challenge_accepted",
                    "match_id": match.match_id,
                    "opponent": chal["challenger_username"],
                })

                challenger_ws = _challenge_ws.get(chal["challenger_id"])
                if challenger_ws:
                    try:
                        await challenger_ws.send_json({
                            "type": "challenge_accepted",
                            "match_id": match.match_id,
                            "opponent": username,
                        })
                    except Exception:
                        pass

            elif msg_type == "decline_challenge":
                challenge_id = data.get("challenge_id")
                chal = matchmaker.pop_pending_challenge(challenge_id)
                if chal and chal["target_id"] == user_id:
                    await ws.send_json({"type": "challenge_declined"})
                    challenger_ws = _challenge_ws.get(chal["challenger_id"])
                    if challenger_ws:
                        try:
                            await challenger_ws.send_json({
                                "type": "challenge_declined",
                                "by": username,
                            })
                        except Exception:
                            pass

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        _challenge_ws.pop(user_id, None)
        try:
            await ws.close()
        except Exception:
            pass
