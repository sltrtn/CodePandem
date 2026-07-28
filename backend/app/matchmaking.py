from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from fastapi import WebSocket

from app.config import CONFIG
from app.lobby import lobby
from app.models import Match, PlayerRoundState, PlayerState, Round
from app.problems import get_problems_for_match
from app.seasons import get_current_season_id


@dataclass
class QueuedPlayer:
    ws: WebSocket
    player_id: str
    username: str
    elo: float
    mode: str = "ranked"
    joined_at: float = 0.0
    range_size: int = 0
    fut: asyncio.Future | None = None


class Matchmaker:
    def __init__(self) -> None:
        self._pool: dict[str, QueuedPlayer] = {}
        self._matches: dict[str, Match] = {}
        self._player_match: dict[str, str] = {}
        self._waiters: dict[str, asyncio.Future[str | None]] = {}
        self._rematch_requests: dict[str, set[str]] = {}
        self._pending_challenges: dict[str, dict] = {}
        self._matcher_task: asyncio.Task | None = None
        self._shutdown: bool = False

    def start(self) -> None:
        if self._matcher_task is None or self._matcher_task.done():
            self._shutdown = False
            self._matcher_task = asyncio.create_task(self._match_loop())

    def stop(self) -> None:
        self._shutdown = True
        if self._matcher_task and not self._matcher_task.done():
            self._matcher_task.cancel()

    @property
    def queue_size(self) -> int:
        return len(self._pool)

    def add_pending_challenge(
        self,
        challenge_id: str,
        challenger_id: str,
        challenger_username: str,
        target_id: str,
    ) -> None:
        self._pending_challenges[challenge_id] = {
            "challenger_id": challenger_id,
            "challenger_username": challenger_username,
            "target_id": target_id,
            "status": "pending",
        }

    def get_pending_challenge(self, challenge_id: str) -> dict | None:
        return self._pending_challenges.get(challenge_id)

    def pop_pending_challenge(self, challenge_id: str) -> dict | None:
        return self._pending_challenges.pop(challenge_id, None)

    async def join_queue(
        self,
        ws: WebSocket,
        player_id: str,
        username: str,
        elo: float,
        mode: str = "ranked",
    ) -> str | None:
        self.start()

        lobby.set_status(player_id, "queued")
        await lobby.broadcast({
            "type": "player_status_changed",
            "player_id": player_id,
            "status": "queued",
            "online_count": lobby.online_count,
        })

        loop = asyncio.get_event_loop()
        fut: asyncio.Future[str | None] = loop.create_future()
        self._waiters[player_id] = fut

        self._pool[player_id] = QueuedPlayer(
            ws=ws,
            player_id=player_id,
            username=username,
            elo=elo,
            mode=mode,
            joined_at=time.time(),
            range_size=CONFIG.MATCHMAKING_INITIAL_RANGE,
            fut=fut,
        )

        try:
            result = await asyncio.wait_for(fut, timeout=CONFIG.MATCHMAKING_MAX_WAIT_S + 2)
            return result
        except asyncio.TimeoutError:
            return None
        finally:
            self._waiters.pop(player_id, None)
            self._pool.pop(player_id, None)
            lobby.set_status(player_id, "online")
            await lobby.broadcast({
                "type": "player_status_changed",
                "player_id": player_id,
                "status": "online",
                "online_count": lobby.online_count,
            })

    async def leave_queue(self, player_id: str) -> None:
        qp = self._pool.pop(player_id, None)
        if qp and qp.fut and not qp.fut.done():
            qp.fut.set_result(None)
        self._waiters.pop(player_id, None)
        lobby.set_status(player_id, "online")
        await lobby.broadcast({
            "type": "player_status_changed",
            "player_id": player_id,
            "status": "online",
            "online_count": lobby.online_count,
        })

    def get_match(self, match_id: str) -> Match | None:
        return self._matches.get(match_id)

    def remove_match(self, match_id: str) -> None:
        match = self._matches.pop(match_id, None)
        if match:
            for pid in match.players:
                self._player_match.pop(pid, None)
                lobby.set_status(pid, "online")

    def request_rematch(self, match_id: str, player_id: str) -> bool:
        if match_id not in self._rematch_requests:
            self._rematch_requests[match_id] = set()
        self._rematch_requests[match_id].add(player_id)
        match = self._matches.get(match_id)
        if not match:
            return False
        return len(self._rematch_requests[match_id]) >= 2

    def clear_rematch(self, match_id: str) -> None:
        self._rematch_requests.pop(match_id, None)

    async def _match_loop(self) -> None:
        while not self._shutdown:
            await asyncio.sleep(CONFIG.MATCHMAKING_SCAN_INTERVAL_S)
            try:
                await self._scan_pool()
            except Exception:
                pass

    async def _scan_pool(self) -> None:
        now = time.time()
        stale: list[str] = []

        for pid, qp in self._pool.items():
            elapsed = now - qp.joined_at
            new_range = CONFIG.MATCHMAKING_INITIAL_RANGE + (
                (int(elapsed) // CONFIG.MATCHMAKING_WIDEN_INTERVAL_S)
                * CONFIG.MATCHMAKING_RANGE_WIDEN
            )
            qp.range_size = min(new_range, CONFIG.MATCHMAKING_MAX_RANGE)

            if (
                qp.ws.client_state.name != "CONNECTED"
                or elapsed >= CONFIG.MATCHMAKING_MAX_WAIT_S
            ):
                stale.append(pid)

        for pid in stale:
            qp = self._pool.pop(pid, None)
            if qp and qp.fut and not qp.fut.done():
                qp.fut.set_result(None)
            self._waiters.pop(pid, None)

        matched: set[str] = set()
        by_mode: dict[str, list[QueuedPlayer]] = {}
        for qp in self._pool.values():
            by_mode.setdefault(qp.mode, []).append(qp)

        for mode, players in by_mode.items():
            players.sort(key=lambda p: p.elo)
            for i, p1 in enumerate(players):
                if p1.player_id in matched:
                    continue
                best: QueuedPlayer | None = None
                best_diff: float = float("inf")
                for p2 in players[i + 1 :]:
                    if p2.player_id in matched:
                        continue
                    if p1.ws is p2.ws:
                        continue
                    diff = abs(p1.elo - p2.elo)
                    if diff <= p1.range_size and diff <= p2.range_size:
                        if diff < best_diff:
                            best_diff = diff
                            best = p2
                if best:
                    matched.add(p1.player_id)
                    matched.add(best.player_id)
                    match = self._create_match(
                        p1.ws,
                        best.ws,
                        p1.player_id,
                        best.player_id,
                        p1.username,
                        best.username,
                        mode=mode,
                        season_id=get_current_season_id(),
                    )
                    if p1.fut and not p1.fut.done():
                        p1.fut.set_result(match.match_id)
                    if best.fut and not best.fut.done():
                        best.fut.set_result(match.match_id)

        for pid in matched:
            self._pool.pop(pid, None)

    def _create_match(
        self,
        ws1: WebSocket,
        ws2: WebSocket,
        pid1: str,
        pid2: str,
        username1: str = "",
        username2: str = "",
        mode: str = "ranked",
        season_id: str | None = None,
    ) -> Match:
        match = Match()
        match.players[pid1] = PlayerState(player_id=pid1, ws=ws1)
        match.players[pid2] = PlayerState(player_id=pid2, ws=ws2)
        match._usernames = {pid1: username1, pid2: username2}
        match.mode = mode
        match.season_id = season_id

        self._player_match[pid1] = match.match_id
        self._player_match[pid2] = match.match_id

        lobby.set_status(pid1, "in_match", match.match_id)
        lobby.set_status(pid2, "in_match", match.match_id)
        asyncio.create_task(
            lobby.broadcast({
                "type": "player_status_changed",
                "player_id": pid1,
                "status": "in_match",
                "match_id": match.match_id,
                "online_count": lobby.online_count,
            })
        )
        asyncio.create_task(
            lobby.broadcast({
                "type": "player_status_changed",
                "player_id": pid2,
                "status": "in_match",
                "match_id": match.match_id,
                "online_count": lobby.online_count,
            })
        )

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
