# CodePandem — Changelog

> Human-readable summary of major repository changes. Not every commit — only meaningful milestones.

---

## 2026-07-26 — M4: Profiles, Leaderboard & Easter Egg

**Created:**
- Navbar component (Battle, Leaderboard, Profile links, sticky)
- LeaderboardScreen (top 50 by ELO, rank colors, clickable rows)
- ProfileScreen (avatar, stats grid, match history)
- Match history display (win/loss/draw badges, opponent links, ELO changes)
- Slater Easter egg (tap username 7 times → purple card → github.com/sltrtn)

**Backend:**
- GET /auth/users/{user_id} — public profile
- GET /auth/users/{user_id}/matches — match history with opponent usernames
- games_played computed field on User

---

## 2026-07-26 — M3: Database & Auth

**Created:**
- SQLite + SQLAlchemy (User, MatchRecord models)
- JWT authentication (register, login, me, leaderboard)
- ELO rating system (K=32, tiers: bronze → diamond)
- WebSocket authentication (token query param)
- Frontend auth (AuthContext, LoginScreen, RegisterScreen, protected routes)
- Match persistence with ELO updates

**Fixed:**
- AmbiguousForeignKeysError on User.matches relationship
- passlib + bcrypt 5.0 incompatibility (pinned bcrypt<4.1)

---

## 2026-07-26 — WebSocket Integration

**Fixed:**
- Starlette `WebSocketState` case mismatch — `"CONNECTED"` not `"connected"` in matchmaking and broadcast checks
- Duel handler player_id lookup — read from query params instead of WebSocket identity check
- Match creation using client player_ids instead of random UUIDs
- DuelContext not reading playerId from localStorage on init
- Missing `winner` field in serialized round data

**Verified:**
- Full E2E flow: queue -> match -> duel -> submit -> scoreboard
- Both players receive match_state, submit code, see duel_state broadcasts

---

## 2026-07-26 — M1: Core Platform

**Created:**
- FastAPI backend with WebSocket and REST endpoints
- Matchmaker with asyncio.Queue + Futures pairing
- Judge with subprocess execution, stdin piping, memory limits, timeouts
- Scoring system with tiered scoring (test cases > speed)
- Anti-cheat system with composite cheat score
- 9 coding problems (3 easy, 3 medium, 3 hard)
- React frontend with Vite, routing, WebSocket hooks
- QueueScreen, DuelScreen, CodeEditor, Scoreboard, ResultsScreen
- CountdownTimer, RoundIndicator
- DuelContext, useWebSocket, useTelemetry
- Dark theme CSS
- 19 backend tests (judge, scoring, anticheat, models)

---

## [Initial]

- Project scaffold created
- Backend/ frontend directory structure established
- Virtual environment configured (Python 3.14.6, Arch Linux)
