from __future__ import annotations

import asyncio

from fastapi import WebSocket

from app.config import CONFIG
from app.models import Match, PlayerRoundState, PlayerState, Round
from app.problems import get_problems_for_match


class Matchmaker:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[tuple[WebSocket, str]] = asyncio.Queue()
        self._matches: dict[str, Match] = {}
        self._player_match: dict[str, str] = {}
        self._waiters: dict[str, asyncio.Future[str | None]] = {}

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    async def join_queue(self, ws: WebSocket, player_id: str) -> str | None:
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[str | None] = loop.create_future()
        self._waiters[player_id] = fut

        await self._queue.put((ws, player_id))

        if self._queue.qsize() >= 2:
            (ws1, pid1) = await self._queue.get()
            (ws2, pid2) = await self._queue.get()

            if ws1.client_state.name != "CONNECTED":
                if ws2.client_state.name == "CONNECTED":
                    await self._queue.put((ws2, pid2))
                self._waiters.pop(pid1, None)
                self._waiters.pop(pid2, None)
                if not fut.done():
                    fut.set_result(None)
                return None
            if ws2.client_state.name != "CONNECTED":
                await self._queue.put((ws1, pid1))
                self._waiters.pop(pid1, None)
                self._waiters.pop(pid2, None)
                if not fut.done():
                    fut.set_result(None)
                return None

            match = self._create_match(ws1, ws2, pid1, pid2)

            if pid1 in self._waiters and not self._waiters[pid1].done():
                self._waiters[pid1].set_result(match.match_id)
            if pid2 in self._waiters and not self._waiters[pid2].done():
                self._waiters[pid2].set_result(match.match_id)

            return match.match_id

        try:
            result = await asyncio.wait_for(fut, timeout=60)
            return result
        except asyncio.TimeoutError:
            return None
        finally:
            self._waiters.pop(player_id, None)

    async def leave_queue(self, ws: WebSocket) -> None:
        items: list = []
        while not self._queue.empty():
            items.append(self._queue.get_nowait())
        for item_ws, item_pid in items:
            if item_ws is not ws:
                await self._queue.put((item_ws, item_pid))

    def get_match(self, match_id: str) -> Match | None:
        return self._matches.get(match_id)

    def remove_match(self, match_id: str) -> None:
        match = self._matches.pop(match_id, None)
        if match:
            for pid in match.players:
                self._player_match.pop(pid, None)

    def _create_match(
        self, ws1: WebSocket, ws2: WebSocket, pid1: str, pid2: str
    ) -> Match:
        match = Match()
        match.players[pid1] = PlayerState(player_id=pid1, ws=ws1)
        match.players[pid2] = PlayerState(player_id=pid2, ws=ws2)

        self._player_match[pid1] = match.match_id
        self._player_match[pid2] = match.match_id

        problems = get_problems_for_match()
        for i, problem in enumerate(problems):
            time_limit = CONFIG.ROUND_TIMES[i]
            rnd = Round(
                round_number=i + 1,
                problem=problem,
                time_limit_s=time_limit,
                status="active" if i == 0 else "pending",
                players={
                    pid1: PlayerRoundState(player_id=pid1),
                    pid2: PlayerRoundState(player_id=pid2),
                },
            )
            match.rounds.append(rnd)

        match.current_round = 1
        match.status = "round_active"
        self._matches[match.match_id] = match
        return match


matchmaker = Matchmaker()
