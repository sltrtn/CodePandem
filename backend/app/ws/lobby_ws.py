from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth import authenticate_ws_token
from app.database import SessionLocal
from app.lobby import lobby

router = APIRouter()


@router.websocket("/ws/lobby")
async def ws_lobby(ws: WebSocket) -> None:
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
        player_id = user.id
        username = user.username
        elo = user.elo
        tier = user.tier
    finally:
        db.close()

    lobby.add_player(player_id, username, ws, elo, tier)

    await ws.send_json({
        "type": "lobby_state",
        "players": lobby.get_online_players(),
        "active_matches": lobby.get_active_matches(),
    })

    await lobby.broadcast({
        "type": "player_joined",
        "player": {
            "player_id": player_id,
            "username": username,
            "status": "online",
            "elo": round(elo, 1),
            "tier": tier,
        },
        "online_count": lobby.online_count,
    })

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "get_players":
                await ws.send_json({
                    "type": "lobby_state",
                    "players": lobby.get_online_players(),
                    "active_matches": lobby.get_active_matches(),
                })

            elif msg_type == "set_status":
                status = data.get("status", "online")
                match_id = data.get("match_id")
                lobby.set_status(player_id, status, match_id)
                await lobby.broadcast({
                    "type": "player_status_changed",
                    "player_id": player_id,
                    "status": status,
                    "match_id": match_id,
                    "online_count": lobby.online_count,
                })

    except WebSocketDisconnect:
        pass
    finally:
        lobby.remove_player(player_id)
        await lobby.broadcast({
            "type": "player_left",
            "player_id": player_id,
            "online_count": lobby.online_count,
        })
        try:
            await ws.close()
        except Exception:
            pass
