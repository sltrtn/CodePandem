# CodePandem — Progress Log

> Chronological work log. Append entries as milestones are reached.

---

## 2026-07-26 — M4: Profiles, Leaderboard & Easter Egg

### Backend:
- Added games_played computed field to User.to_dict()
- GET /auth/users/{user_id} — public user profile
- GET /auth/users/{user_id}/matches — match history with opponent usernames

### Frontend:
- **Navbar** — sticky top nav with Battle, Leaderboard, Profile links, username + tier badge
- **LeaderboardScreen** — top 50 players sorted by ELO, gold/silver/bronze rank colors, clickable rows link to profiles
- **ProfileScreen** — avatar (first letter), username, tier badge, 6-stat grid (ELO, Games, Wins, Losses, Draws, Win Rate)
- **Match history** — win/loss/draw badges, opponent links, round count, date, ELO change (+/-)
- **Slater Easter egg** — tap username 7 times on profile, purple card (#1A0040) fades in with "Slater" in #D4AAFF, tagline "The one who started it all.", link to github.com/sltrtn
- Countdown hint "X more..." appears after first tap
- Reset counter when navigating to different profile
- Matches Meluko's implementation exactly (same colors, same behavior)

### Verified:
- All 19 backend tests pass
- Frontend builds clean
- Leaderboard shows all users sorted by ELO
- Profile shows user stats and match history
- Easter egg triggers after 7 taps on username

---

## 2026-07-26 — M3: Database & Auth

### Database layer:
- SQLite + SQLAlchemy with User and MatchRecord models
- User: id, username, password_hash, elo (1000 start), wins, losses, draws, tier
- MatchRecord: id, player1_id, player2_id, winner_id, elo_changes, rounds_played
- Fixed AmbiguousForeignKeysError on User.matches relationship
- Fixed passlib + bcrypt 5.0 incompatibility (pinned bcrypt<4.1)

### Authentication:
- JWT tokens (HS256, 7-day expiry)
- bcrypt password hashing
- POST /auth/register (3-30 char username, 6+ char password)
- POST /auth/login (returns JWT + user profile)
- GET /auth/me (authenticated user profile)
- GET /auth/leaderboard (top 50 by ELO)
- WebSocket auth via token query parameter

### ELO system:
- K-factor = 32, standard ELO formula
- Tiers: bronze (<1200), silver (1200-1599), gold (1600-1999), platinum (2000-2399), diamond (2400+)
- Match records persisted with ELO changes
- Win/loss/draw tracked per user

### Frontend auth:
- AuthContext (login, register, logout, token storage)
- LoginScreen + RegisterScreen with form validation
- Protected routes (redirect to /login if unauthenticated)
- QueueScreen shows username, ELO, tier badge, logout button
- DuelContext uses JWT token for WebSocket auth

### Verified:
- Register: creates user, returns JWT + profile
- Login: validates credentials, returns JWT + profile
- Duplicate username: 409 Conflict
- Wrong password: 401 Unauthorized
- All 19 backend tests pass
- Frontend builds clean

---

## 2026-07-26 — WebSocket Integration + Bug Fixes

### WebSocket bugs fixed:
- **Starlette WebSocketState case mismatch** — `ws.client_state.name` returns `"CONNECTED"` (uppercase), not `"connected"`. Every `!= "connected"` check in matchmaking and broadcast was silently failing, rejecting valid connections and preventing message delivery.
- **Duel handler player_id lookup** — Old code used `ps.ws is ws` to identify the player, but the duel WebSocket is a new connection (different object from the queue WebSocket). Fixed to read `player_id` from `ws.query_params`.
- **Match creation UUID mismatch** — `Match.add_player()` generated random UUIDs, but clients send player_ids like `"player1"`. The duel handler couldn't find the player in `match.players`. Fixed `_create_match` to use provided `pid1`/`pid2` directly.
- **DuelContext missing initial player_id** — `playerId` started as `null`, causing WebSocket to connect without `?player_id=`, which the server rejected. Fixed to initialize from `localStorage.getItem("playerId")`.
- **Missing winner in serialized round data** — `ResultsScreen` expected `r.winner` but `_serialize_round()` didn't include it. Added `winner` field to `Round` model and serialization.

### E2E verification:
- Queue -> Matchmaking -> Duel -> Submit -> Scoreboard all working
- P1 correct (FizzBuzz 3/3, score=1.01), P2 wrong (print(42), 0/3, score=0.01)
- Both players see each other's submissions via broadcast
- All 19 backend tests pass, frontend builds clean

---

## 2026-07-26 — M1: Core Platform (initial build)

### Backend:
- FastAPI app with CORS, WebSocket and REST routers
- Data models: Match, PlayerState, Round, PlayerRoundState, SubmissionResult, CheatScore, Telemetry, Problem
- Config: frozen dataclass with all thresholds (submission timeout, memory limit, round times, anti-cheat thresholds)
- 9 problems: Two Sum, Reverse String, FizzBuzz, Valid Parentheses, Longest Substring, Group Anagrams, Merge Intervals, Minimum Window Substring, Trapping Rain Water
- Judge: `_build_wrapper()` creates Python script with stdin piping, `run_submission()` runs code per test case with subprocess + resource limits
- Scoring: `score_submission()` (tiered), `determine_round_winner()`, `determine_match_winner()`
- Anti-cheat: `calculate_cheat_score()` with 4 rules (speed threshold 0.25, paste detection 0.30, tab switches 0.20, keystroke anomaly 0.15)
- Matchmaker: asyncio.Queue + Futures pairing, match creation with 3 rounds
- Queue WebSocket: join_queue, match_found, leave_queue
- Duel WebSocket: submit, duel_state broadcast, round timer, round_over, match_over
- REST: GET /health, GET /problems, POST /submit

### Frontend:
- React 19 + Vite 8 + react-router-dom 7
- QueueScreen: WebSocket to /ws/queue, spinner, auto-navigate on match_found
- DuelScreen: round indicator, countdown timer, problem panel, code editor, scoreboard
- CodeEditor: textarea with onPaste/onKeyDown telemetry, submit button
- Scoreboard: both players' wins, scores, cheat flag icons
- ResultsScreen: VICTORY/DEFEAT, round-by-round breakdown
- RoundIndicator: 3 dots with active/won states
- CountdownTimer: mm:ss, red warning at 30s
- DuelContext: match state, round data, players, submitCode, timer
- useWebSocket: connect, send, subscribe pattern
- useTelemetry: paste events, tab switches, keystroke counting
- Dark theme CSS for all components

### Tests:
- 6 judge tests (correct, wrong, syntax error, runtime error, timeout, multiple test cases)
- 5 scoring tests (perfect fast, partial, zero, round winner, round tie, match winner)
- 4 anticheat tests (normal low, paste fast high, tab switches, impossible speed)
- 3 model tests (match creation, round defaults, player state defaults)
