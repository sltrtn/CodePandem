# Lesson 1 — Mental Model: What is CodePandem?

## The problem CodePandem solves

Coding practice is usually lonely. You solve problems alone, compare yourself to a leaderboard later, and there is no social pressure or real-time competition. CodePandem makes coding a live 1v1 sport: two players get the same problems, race the clock, and see each other's progress in real time.

## The high-level flow

```
Player A opens app
       ↓
Logs in / registers (JWT)
       ↓
Joins ranked queue  ─────────┐
                              ↓
                        Matchmaker pairs by ELO
                              ↓
Player A ←──── match_found ───┘
Player B ←──── match_found
       ↓
Both connect to /ws/duel/{match_id}
       ↓
Round 1 (easy) starts ──→ both submit code
       ↓
Judge executes code, anti-cheat runs, scores update
       ↓
Round 2 (medium), Round 3 (hard)
       ↓
Match over → ELO updated → leaderboard updated
```

## HTTP vs WebSocket

**HTTP** is request/response: the client asks, the server answers, then the connection closes. Good for login, fetching problems, submitting once.

**WebSocket** is a persistent two-way connection: the server can push data to the client at any time. Essential for live duels because both players need instant updates when someone submits.

In your code:
- HTTP routes live in `backend/app/routers/`.
- WebSocket routes live in `backend/app/ws/`.

## The three main WebSocket endpoints

| Endpoint | Purpose |
|---|---|
| `/ws/queue` | Queue for ranked/unranked matchmaking |
| `/ws/duel/{match_id}` | Live duel: submit code, chat, round timers |
| `/ws/lobby` | Online presence, active matches, spectators |

## In-memory state vs database state

**In-memory (`app/models.py` dataclasses):** active matches, queued players, online lobby. Fast, but lost on server restart.

**Database (`app/models_db.py` SQLAlchemy):** users, match records, friendships, refresh tokens, seasons. Persistent.

This split is important: a real-money platform would persist active matches too, but for a portfolio project the in-memory state keeps the code simple while still demonstrating real-time systems thinking.

## Why this matters in an interview

You can say:

> "CodePandem is a real-time competitive coding platform. The backend is FastAPI with native WebSocket support. Match state lives in memory for speed; user records, ELO, and match history live in SQLite. The judge is a separate service so untrusted user code never runs inside the main backend."

## Common trap

**"Why not just use HTTP polling?"**

Strong answer: polling adds latency and wastes resources. WebSocket keeps one open connection and pushes state instantly. In a duel, a 500ms poll delay would make the live scoreboard feel broken.

## Self-check

1. Why does a live duel need WebSocket instead of HTTP?
2. What state is in-memory? What is in the database?
3. Why is the judge a separate service?
4. Walk through the flow from "click Battle" to "match over."
5. What would break if the server restarted mid-match?

## Code map

| Concept | File |
|---|---|
| FastAPI app + routers | `backend/app/main.py` |
| Queue WebSocket | `backend/app/ws/queue.py` |
| Duel WebSocket | `backend/app/ws/duel.py` |
| Match dataclass | `backend/app/models.py` |
| User DB model | `backend/app/models_db.py` |
| Lobby state | `backend/app/lobby.py` |
