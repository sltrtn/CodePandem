# CodePandem

Real-time 1v1 coding battles with strategic sabotage, anti-cheat detection, and post-match learning.

## Quick Start

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Server runs on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

## Architecture

```
Player A ──┐
           ├── FastAPI (WebSocket) ── Matchmaker (asyncio.Queue)
Player B ──┘         │
                     ├── Judge (subprocess + resource limits)
                     ├── Scoring (tiered: test cases + speed tiebreaker)
                     └── Anti-cheat (paste detection + tab tracking)
```

## M1 Scope

### What's Included
- Matchmaking queue with real-time WebSocket sync
- 3-round escalating matches (easy → medium → hard, 3min → 5min → 8min)
- Tiered scoring: test cases (primary) + execution speed (tiebreaker)
- Code execution via process-isolated subprocess (5s timeout, 128MB memory cap)
- Anti-cheat telemetry: paste detection, tab switch tracking, keystroke analysis
- 9 hardcoded problems (3 per difficulty)
- Dark-themed React frontend

### What's Not Included (by design)
- No database, no auth, no Redis — all M3+
- No Docker sandboxing — subprocess isolation, Docker in M5
- No Monaco editor — plain textarea, upgrade later
- No ELO ratings — M3+
- No spectator mode — M4+

## Anti-Cheat

Every submission sends behavioral telemetry:
- Paste events (was code pasted? how much? when?)
- Tab switches (did the player leave the tab to look up answers?)
- Keystroke count and speed
- Time since match start

The server calculates a cheat score (0.0–1.0) using weighted rules:
- Speed: submission under difficulty threshold (easy: 8s, medium: 15s, hard: 25s)
- Paste: zero keystrokes + large code = likely pasted
- Tabs: multiple switches, especially before correct submissions
- Keystrokes: impossibly fast or uniform typing speed

Flagged submissions show a warning on the scoreboard. Repeated flags trigger review.

## Scoring

Tiered system — test cases are primary, speed is tiebreaker:

```
base = test_cases_passed / test_cases_total    # 0.0 to 1.0
speed = max(0, 1 - time_ms / time_limit_ms)    # 0.0 to 1.0
score = base + (speed × 0.01)                   # speed adds at most 0.01
```

A 4/5 solution always beats a 3/5 solution regardless of speed.
Speed only matters when test case counts are equal.

## API

### REST
- `GET /health` — server status
- `GET /problems` — list available problems
- `POST /submit` — submit code (debug endpoint)

### WebSocket
- `/ws/queue` — matchmaking queue
- `/ws/duel/{match_id}?player_id={id}` — live duel

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```
