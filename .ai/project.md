# CodePandem — Project Overview

> Living documentation for the CodePandem real-time 1v1 competitive coding platform.

---

## What It Is

CodePandem is a **real-time 1v1 competitive coding battle platform**. Two players queue, get matched, and battle through escalating rounds of coding problems — easy to hard — with a live timer, anti-cheat monitoring, and tiered scoring.

**Core thesis:** Competitive coding is more engaging head-to-head. CodePandem turns it into a fast-paced duel with escalating difficulty and real-time feedback.

---

## Architecture

### Backend (FastAPI + WebSocket)

```
main.py                          ← FastAPI app, CORS, router mounting
├── routers/
│   ├── health.py                ← GET /health
│   └── submissions.py           ← POST /submit (REST fallback)
├── ws/
│   ├── queue.py                 ← /ws/queue — matchmaking lobby
│   └── duel.py                  ← /ws/duel/{match_id} — live battle
├── matchmaking.py               ← Matchmaker (asyncio.Queue + Futures)
├── judge.py                     ← Subprocess code execution
├── scoring.py                   ← Tiered scoring (test cases > speed)
├── anticheat.py                 ← Composite cheat detection
├── problems.py                  ← 9 hardcoded problems (3 easy, 3 med, 3 hard)
├── config.py                    ← Frozen Config dataclass
└── models.py                    ← All dataclasses (Match, Round, etc.)
```

### Frontend (React + Vite)

```
frontend/src/
├── App.jsx                      ← BrowserRouter with routes
├── main.jsx                     ← React entry point
├── components/
│   ├── QueueScreen.jsx          ← Queue lobby with WebSocket
│   ├── DuelScreen.jsx           ← Main battle view
│   ├── CodeEditor.jsx           ← Textarea with anti-cheat telemetry
│   ├── ProblemPanel.jsx         ← Problem description display
│   ├── Scoreboard.jsx           ← Live scores + cheat flags
│   ├── ResultsScreen.jsx        ← Match results with round breakdown
│   ├── RoundIndicator.jsx       ← Round dots + label
│   └── CountdownTimer.jsx       ← Round timer
├── context/
│   └── DuelContext.jsx          ← React context for match state
├── hooks/
│   ├── useWebSocket.js          ← Custom WebSocket hook
│   └── useTelemetry.js          ← Anti-cheat event collection
└── styles/
    └── app.css                  ← Full dark theme
```

### Flow

```
1. Player opens / → QueueScreen
2. QueueScreen opens WebSocket to /ws/queue
3. Player sends { type: "join_queue", player_id: "..." }
4. Matchmaker pairs two players → sends { type: "match_found", match_id, player_id }
5. Frontend navigates to /duel/{match_id}
6. DuelScreen opens WebSocket to /ws/duel/{match_id}?player_id=...
7. Server sends match_state with Round 1 (Easy, 3min)
8. Players write code, submit via WebSocket
9. Server judges code, broadcasts duel_state
10. Round ends (timer expires) → round_over → next round (Medium, 5min → Hard, 8min)
11. First to 2 round wins takes the match → match_over
```

---

## Key Design Decisions

- **Tiered scoring**: Test cases are primary rank, speed is tiebreaker only. Mathematically impossible for speed to overcome test case difference.
- **Anti-cheat**: Paste detection, tab switch tracking, keystroke analysis, submission speed thresholds — composite cheat score 0.0-1.0, flagged at >0.5.
- **Subprocess judge**: Each test case runs user code in a subprocess with `resource.setrlimit` for 128MB memory cap and 5s timeout. Code runs once per test case with stdin piped.
- **No DB, no Redis (M1)**: All state in memory. Matchmaker uses asyncio.Queue + Futures for pairing.
- **WebSocket-only real-time**: No polling, no SSE. Both queue and duel use WebSockets.

---

## External Services

| Service | Purpose | Auth Method |
|---|---|---|
| Python subprocess | Code execution sandbox | None (local) |

No external APIs, databases, or authentication services. Pure self-contained platform.

---

## Key Dependencies

### Backend
- `fastapi` — Web framework
- `uvicorn[standard]` — ASGI server with WebSocket support
- `websockets` — WebSocket protocol (used in tests)

### Frontend
- `react` 19.2 — UI framework
- `react-dom` 19.2 — DOM rendering
- `react-router-dom` 7.18 — Client-side routing
- `vite` 8.1 — Build tool and dev server
- `@vitejs/plugin-react` 6.0 — React Fast Refresh for Vite

---

## Problem Bank

| ID | Title | Difficulty | Test Cases |
|---|---|---|---|
| easy_1 | Two Sum | Easy | 3 |
| easy_2 | Reverse String | Easy | 3 |
| easy_3 | FizzBuzz | Easy | 3 |
| med_1 | Valid Parentheses | Medium | 4 |
| med_2 | Longest Substring Without Repeating | Medium | 4 |
| med_3 | Group Anagrams | Medium | 2 |
| hard_1 | Merge Intervals | Hard | 3 |
| hard_2 | Minimum Window Substring | Hard | 3 |
| hard_3 | Trapping Rain Water | Hard | 3 |

---

## Run Commands

```bash
# Backend
cd /home/mad/codepandem/backend
/home/mad/codepandem/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd /home/mad/codepandem/frontend
npm run dev

# Tests
cd /home/mad/codepandem/backend
/home/mad/codepandem/backend/venv/bin/python -m pytest tests/ -v
```
