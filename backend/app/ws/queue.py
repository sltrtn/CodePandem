from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth import authenticate_ws_token
from app.database import SessionLocal
from app.matchmaking import matchmaker

router = APIRouter()


@router.websocket("/ws/queue")
async def ws_queue(ws: WebSocket) -> None:
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
    finally:
        db.close()

    await ws.send_json({
        "type": "queued",
        "position": matchmaker.queue_size,
        "player_id": player_id,
        "username": username,
    })

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "join_queue":
                match_id = await matchmaker.join_queue(ws, player_id)
                if match_id:
                    await ws.send_json({
                        "type": "match_found",
                        "match_id": match_id,
                        "player_id": player_id,
                        "username": username,
                    })
                    break
                else:
                    await ws.send_json({"type": "error", "message": "Timeout"})
                    break

            elif msg_type == "leave_queue":
                await matchmaker.leave_queue(ws)
                await ws.send_json({"type": "left_queue"})
                break

    except WebSocketDisconnect:
        await matchmaker.leave_queue(ws)
    finally:
        try:
            await ws.close()
        except Exception:
            pass
