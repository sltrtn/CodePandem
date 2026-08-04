# Lesson 4 — Matchmaking: ELO-Aware Pool Matching

## What this lesson covers

- How players enter the queue
- How the matchmaker pairs them
- ELO range widening
- Ranked vs unranked modes

## Joining the queue

File: `backend/app/ws/queue.py`

```python
@router.websocket("/ws/queue")
async def ws_queue(ws: WebSocket) -> None:
    await ws.accept()
    token = ws.query_params.get("token")
    user = authenticate_ws_token(token, db)
    await ws.send_json({"type": "connected", ...})

    while True:
        data = await ws.receive_json()
        msg_type = data.get("type")
        if msg_type == "join_queue":
            await ws.send_json({"type": "queued", ...})
            match_id = await matchmaker.join_queue(ws, player_id, username, elo, mode)
            if match_id:
                await ws.send_json({"type": "match_found", ...})
```

The player first connects, then explicitly sends `join_queue`. This prevents accidental queueing.

## The matchmaker

File: `backend/app/matchmaking.py`

```python
class Matchmaker:
    def __init__(self):
        self._pool: dict[str, QueuedPlayer] = {}
        self._matches: dict[str, Match] = {}
        self._player_match: dict[str, str] = {}
        self._matcher_task: asyncio.Task | None = None
```

A single background `_match_loop` scans the pool every second.

## Range widening

Each player has a `range_size` that grows over time:

```python
new_range = CONFIG.MATCHMAKING_INITIAL_RANGE + (
    (int(elapsed) // CONFIG.MATCHMAKING_WIDEN_INTERVAL_S)
    * CONFIG.MATCHMAKING_RANGE_WIDEN
)
qp.range_size = min(new_range, CONFIG.MATCHMAKING_MAX_RANGE)
```

- Initial range: ±100 ELO
- Grows by ±25 every 5 seconds
- Caps at ±400 ELO
- Max wait: 60 seconds

This balances fairness (close ELOs) with queue time (wider over time).

## Pairing algorithm

```python
players.sort(key=lambda p: p.elo)
for i, p1 in enumerate(players):
    best = None
    best_diff = float("inf")
    for p2 in players[i + 1:]:
        diff = abs(p1.elo - p2.elo)
        if diff <= p1.range_size and diff <= p2.range_size and diff < best_diff:
            best = p2
            best_diff = diff
    if best:
        # create match
```

It finds the closest two players within overlapping ranges. This is a greedy nearest-neighbor approach, not a perfect global matching, but it is fast and good enough.

## Ranked vs unranked

Mode is stored on the `QueuedPlayer`. Mode is also stored on the `Match` and affects whether ELO changes are persisted.

## Why this matters in an interview

You can say:

> "Matchmaking is a pool-based ELO-aware system. Players start with a ±100 ELO range and it widens every 5 seconds up to ±400. The scanner finds the closest pair whose ranges overlap. Ranked matches affect ELO; unranked and custom matches do not."

## Common trap

**"What if there is only one player?"**

After `MATCHMAKING_MAX_WAIT_S` (60s) the player times out. If they disconnect, they are removed from the pool.

## Self-check

1. How does a player join the queue?
2. What is the initial ELO range and how does it widen?
3. How are players paired?
4. What is the difference between ranked and unranked mode?
5. What happens if a player waits too long?

## Code map

| Concept | File |
|---|---|
| Queue WebSocket | `backend/app/ws/queue.py` |
| Matchmaker | `backend/app/matchmaking.py` |
| Match creation | `backend/app/matchmaking.py` `_create_match` |
| Config constants | `backend/app/config.py` |
