# CodePandem — Roadmap

---

## Legend
- Completed
- In Progress
- Planned
- Blocked

---

## Completed Milestones

### M1: Core Platform
- Backend scaffold (FastAPI + WebSocket)
- Data models (Match, Round, PlayerState, SubmissionResult, Telemetry, Problem)
- Config system (frozen dataclass with all thresholds)
- 9 hardcoded problems (3 easy, 3 medium, 3 hard)
- Judge (subprocess execution with stdin piping, 128MB memory cap, 5s timeout)
- Scoring system (tiered: test cases primary, speed tiebreaker)
- Anti-cheat system (paste detection, tab switches, keystroke analysis, submission speed)
- Matchmaking (asyncio.Queue + Futures, two-player pairing)
- Queue WebSocket (/ws/queue — join_queue, match_found, leave_queue)
- Duel WebSocket (/ws/duel/{match_id} — submit, duel_state, round_over, match_over)
- Round lifecycle (timer, auto-finish, winner determination)
- Match lifecycle (3 rounds, escalating difficulty, first-to-2 wins)
- REST endpoints (GET /health, GET /problems, POST /submit)
- Frontend scaffold (React + Vite + react-router-dom)
- QueueScreen (WebSocket connection, spinner, match_found navigation)
- DuelScreen (round indicator, problem panel, code editor, scoreboard)
- CodeEditor (textarea with paste/tab/keystroke telemetry tracking)
- Scoreboard (live scores, cheat flag icons)
- ResultsScreen (VICTORY/DEFEAT, round-by-round breakdown)
- RoundIndicator (active round dot, won dots)
- CountdownTimer (mm:ss, low warning at 30s)
- DuelContext (React context, match state management)
- useWebSocket hook (connect, send, subscribe)
- useTelemetry hook (paste events, tab switches, keystroke counting)
- Dark theme CSS (full styling for all components)
- Backend tests (19 tests: judge 6, scoring 5, anticheat 4, models 3)

### M2: WebSocket Integration (this session)
- Fixed Starlette WebSocketState case mismatch (CONNECTED vs connected)
- Fixed duel handler player_id lookup (query params instead of ws identity)
- Fixed match creation to use client player_ids instead of random UUIDs
- Fixed DuelContext to initialize playerId from localStorage
- Added Round.winner field + serialization
- Full E2E verified: queue -> match -> duel -> submit -> scoreboard

---

## Completed Milestones

### M1: Core Platform
- Backend scaffold (FastAPI + WebSocket)
- Data models (Match, Round, PlayerState, SubmissionResult, Telemetry, Problem)
- Config system (frozen dataclass with all thresholds)
- 9 hardcoded problems (3 easy, 3 medium, 3 hard)
- Judge (subprocess execution with stdin piping, 128MB memory cap, 5s timeout)
- Scoring system (tiered: test cases primary, speed tiebreaker)
- Anti-cheat system (paste detection, tab switches, keystroke analysis, submission speed)
- Matchmaking (asyncio.Queue + Futures, two-player pairing)
- Queue WebSocket (/ws/queue — join_queue, match_found, leave_queue)
- Duel WebSocket (/ws/duel/{match_id} — submit, duel_state, round_over, match_over)
- Round lifecycle (timer, auto-finish, winner determination)
- Match lifecycle (3 rounds, escalating difficulty, first-to-2 wins)
- REST endpoints (GET /health, GET /problems, POST /submit)
- Frontend scaffold (React + Vite + react-router-dom)
- QueueScreen (WebSocket connection, spinner, match_found navigation)
- DuelScreen (round indicator, problem panel, code editor, scoreboard)
- CodeEditor (textarea with paste/tab/keystroke telemetry tracking)
- Scoreboard (live scores, cheat flag icons)
- ResultsScreen (VICTORY/DEFEAT, round-by-round breakdown)
- RoundIndicator (active round dot, won dots)
- CountdownTimer (mm:ss, low warning at 30s)
- DuelContext (React context, match state management)
- useWebSocket hook (connect, send, subscribe)
- useTelemetry hook (paste events, tab switches, keystroke counting)
- Dark theme CSS (full styling for all components)
- Backend tests (19 tests: judge 6, scoring 5, anticheat 4, models 3)

### M2: WebSocket Integration
- Fixed Starlette WebSocketState case mismatch (CONNECTED vs connected)
- Fixed duel handler player_id lookup (query params instead of ws identity)
- Fixed match creation to use client player_ids instead of random UUIDs
- Fixed DuelContext to initialize playerId from localStorage
- Added Round.winner field + serialization
- Full E2E verified: queue -> match -> duel -> submit -> scoreboard

### M3: Database & Auth
- SQLite + SQLAlchemy (persistent users, matches, stats)
- User model: id, username, password_hash, elo, wins, losses, draws, tier, games_played
- MatchRecord model: id, player1_id, player2_id, winner_id, elo_changes, rounds_played
- JWT authentication (HS256, 7-day expiry, bcrypt password hashing)
- POST /auth/register, POST /auth/login, GET /auth/me
- GET /auth/leaderboard (top 50 by ELO)
- GET /auth/users/{id} (public profile)
- GET /auth/users/{id}/matches (match history)
- WebSocket authentication via token query parameter
- ELO rating system (K=32, standard formula)
- Tier system (bronze/silver/gold/platinum/diamond)
- Match persistence to database with ELO updates on match completion
- Frontend: AuthContext, LoginScreen, RegisterScreen, protected routes
- Frontend: QueueScreen shows user info + logout

### M4: Profiles, Leaderboard & Easter Egg
- Navbar component (Battle, Leaderboard, Profile links)
- LeaderboardScreen (top players sorted by ELO, gold/silver/bronze rank colors)
- ProfileScreen (avatar, stats grid, match history with ELO changes)
- Match history: win/loss/draw badges, opponent links, elo change (+/-)
- GET /auth/users/{id} and GET /auth/users/{id}/matches endpoints
- games_played computed field on User model
- Slater Easter egg: tap username 7 times on profile, purple card fades in linking to github.com/sltrtn
- Matches Meluko's implementation: tap-to-reveal, countdown hint, same color scheme

---

## Current Milestone

### Lobby & Spectating
- Online players visible in lobby
- Spectate active matches
- Rematch system after match ends

---

## Future Milestones

### Polish & UX
- Match countdown (3-2-1 before first round)
- Player disconnect handling (opponent wins)
- Sound effects (match found, round start, submission)
- Animations (score update, round transition, victory)
- Mobile responsive layout
- Loading states / skeletons

### Anti-Cheat Enhancement
- Mouse movement tracking
- Copy/paste from external source detection
- Code similarity detection (between submissions)
- Plagiarism flagging

### Features
- Player profiles and stats (win/loss, rating)
- Leaderboard / ELO ranking
- Custom problem sets
- Spectator mode
- Rematch system
- Chat during match

### Infrastructure
- Database persistence (SQLite or PostgreSQL)
- User authentication
- Rate limiting
- Health monitoring / metrics
- Docker deployment

---

## Technical Debt

- No database — all state in memory, lost on restart
- No authentication — player_id is client-generated (trivially spoofable)
- Anti-cheat is client-reported telemetry (can be faked)
- 9 hardcoded problems (need more variety)
- No rematch / queue-back-after-match
- Frontend has no error boundary or fallback UI
- No unit tests for frontend
- Judge uses `sys.exit()` wrapper which may not catch all edge cases
- WebSocket handler has bare `except Exception: pass` (swallows errors silently)
