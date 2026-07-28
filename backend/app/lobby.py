from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from fastapi import WebSocket


@dataclass
class OnlinePlayer:
    player_id: str
    username: str
    ws: WebSocket
    status: str = "online"  # online | queued | in_match | spectating
    match_id: str | None = None
    elo: float = 1000.0
    tier: str = "bronze"


class Lobby:
    def __init__(self) -> None:
        self._players: dict[str, OnlinePlayer] = {}
        self._watchers: dict[str, WebSocket] = {}

    @property
    def online_count(self) -> int:
        return len(self._players)

    def add_player(self, player_id: str, username: str, ws: WebSocket, elo: float, tier: str) -> None:
        self._players[player_id] = OnlinePlayer(
            player_id=player_id,
            username=username,
            ws=ws,
            elo=elo,
            tier=tier,
        )

    def remove_player(self, player_id: str) -> None:
        self._players.pop(player_id, None)

    def set_status(self, player_id: str, status: str, match_id: str | None = None) -> None:
        p = self._players.get(player_id)
        if p:
            p.status = status
            p.match_id = match_id

    def get_player(self, player_id: str) -> OnlinePlayer | None:
        return self._players.get(player_id)

    def get_online_players(self) -> list[dict]:
        return [
            {
                "player_id": p.player_id,
                "username": p.username,
                "status": p.status,
                "match_id": p.match_id,
                "elo": round(p.elo, 1),
                "tier": p.tier,
            }
            for p in self._players.values()
        ]

    def get_active_matches(self) -> list[dict]:
        seen: set[str] = set()
        matches = []
        for p in self._players.values():
            if p.match_id and p.match_id not in seen:
                seen.add(p.match_id)
                matches.append({
                    "match_id": p.match_id,
                    "player_id": p.player_id,
                    "username": p.username,
                })
        return matches

    async def broadcast(self, message: dict) -> None:
        stale: list[str] = []
        for pid, p in self._players.items():
            if p.ws.client_state.name == "CONNECTED":
                try:
                    await p.ws.send_json(message)
                except Exception:
                    stale.append(pid)
            else:
                stale.append(pid)
        for pid in stale:
            self._players.pop(pid, None)

    def add_watcher(self, watcher_id: str, ws: WebSocket) -> None:
        self._watchers[watcher_id] = ws

    def remove_watcher(self, watcher_id: str) -> None:
        self._watchers.pop(watcher_id, None)

    async def broadcast_to_watchers(self, match_id: str, message: dict) -> None:
        stale: list[str] = []
        for wid, ws in self._watchers.items():
            if ws.client_state.name == "CONNECTED":
                try:
                    await ws.send_json(message)
                except Exception:
                    stale.append(wid)
            else:
                stale.append(wid)
        for wid in stale:
            self._watchers.pop(wid, None)


lobby = Lobby()
