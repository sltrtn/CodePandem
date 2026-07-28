import asyncio

import pytest

from app.config import CONFIG
from app.matchmaking import Matchmaker
from app.seasons import get_current_season


class FakeWS:
    def __init__(self, connected=True):
        self.client_state = type(
            "State", (), {"name": "CONNECTED" if connected else "DISCONNECTED"}
        )()


@pytest.mark.asyncio
async def test_matchmaker_pairs_close_elo():
    mm = Matchmaker()
    mm.start()
    ws1 = FakeWS()
    ws2 = FakeWS()

    task1 = asyncio.create_task(mm.join_queue(ws1, "p1", "alice", 1100, "ranked"))
    task2 = asyncio.create_task(mm.join_queue(ws2, "p2", "bob", 1120, "ranked"))
    r1, r2 = await asyncio.wait_for(asyncio.gather(task1, task2), timeout=5)

    assert r1 == r2
    assert isinstance(r1, str)
    assert mm.get_match(r1) is not None
    mm.stop()


@pytest.mark.asyncio
async def test_matchmaker_respects_mode_separation(monkeypatch):
    monkeypatch.setattr("app.matchmaking.CONFIG.MATCHMAKING_MAX_WAIT_S", 1)
    mm = Matchmaker()
    mm.start()
    ws1 = FakeWS()
    ws2 = FakeWS()

    task1 = asyncio.create_task(mm.join_queue(ws1, "p1", "alice", 1100, "ranked"))
    task2 = asyncio.create_task(mm.join_queue(ws2, "p2", "bob", 1100, "unranked"))
    r1, r2 = await asyncio.wait_for(asyncio.gather(task1, task2), timeout=5)

    # Both should timeout because modes differ
    assert r1 is None
    assert r2 is None
    mm.stop()


def test_range_widening():
    elapsed = 12
    new_range = CONFIG.MATCHMAKING_INITIAL_RANGE + (
        (int(elapsed) // CONFIG.MATCHMAKING_WIDEN_INTERVAL_S)
        * CONFIG.MATCHMAKING_RANGE_WIDEN
    )
    assert new_range > CONFIG.MATCHMAKING_INITIAL_RANGE


def test_season_auto_created():
    season = get_current_season()
    assert season.id
    assert season.active
    assert "Season" in season.name
