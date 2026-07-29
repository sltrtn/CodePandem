from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth import authenticate_ws_token
from app.database import SessionLocal
from app.matchmaking import matchmaker
from app.models_db import User

router = APIRouter()


async def _send_status(player_id: str, mode: str, elo: float) -> None:
    qp = matchmaker._pool.get(player_id)
    if not qp:
        return
    elapsed = int(time.time() - qp.joined_at)
    try:
        await qp.ws.send_json({
            "type": "queue_status",
            "elapsed_s": elapsed,
            "range": qp.range_size,
            "mode": mode,
            "players_in_queue": matchmaker.queue_size,
            "elo": round(elo, 1),
        })
    except Exception:
        pass


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
        elo = user.elo
    finally:
        db.close()

    await ws.send_json({
        "type": "connected",
        "player_id": player_id,
        "username": username,
        "elo": round(elo, 1),
        "players_in_queue": matchmaker.queue_size,
    })

    mode: str = "ranked"

    async def _status_loop() -> None:
        while True:
            await asyncio.sleep(2)
            await _send_status(player_id, mode, elo)

    status_task: asyncio.Task | None = None

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "join_queue":
                mode = data.get("mode", "ranked") or "ranked"
                if mode not in ("ranked", "unranked"):
                    mode = "ranked"

                await ws.send_json({
                    "type": "queued",
                    "position": matchmaker.queue_size,
                    "player_id": player_id,
                    "username": username,
                    "elo": round(elo, 1),
                })

                status_task = asyncio.create_task(_status_loop())

                match_id = await matchmaker.join_queue(
                    ws, player_id, username, elo, mode
                )
                if status_task and not status_task.done():
                    status_task.cancel()

                if match_id:
                    await ws.send_json({
                        "type": "match_found",
                        "match_id": match_id,
                        "player_id": player_id,
                        "username": username,
                        "mode": mode,
                    })
                    break
                else:
                    await ws.send_json({"type": "queue_timeout"})
                    break

            elif msg_type == "leave_queue":
                await matchmaker.leave_queue(player_id)
                await ws.send_json({"type": "left_queue"})
                break

    except WebSocketDisconnect:
        await matchmaker.leave_queue(player_id)
    except Exception:
        await matchmaker.leave_queue(player_id)
    finally:
        if status_task and not status_task.done():
            status_task.cancel()
        try:
            await ws.close()
        except Exception:
            pass
