# CodePandem — Development Roadmap

## Phase 1: Core Platform ✅
- FastAPI backend with WebSocket support
- React frontend with dark theme
- Judge system, scoring, anti-cheat, 9 problems

## Phase 2: WebSocket Integration ✅
- Matchmaking queue, real-time duel, round lifecycle

## Phase 3: Database & Auth ✅
- SQLite, JWT, ELO, match persistence

## Phase 4: Profiles, Leaderboard & Easter Egg ✅
- Leaderboard, profiles, Slater Easter egg

## Phase 5: Lobby, Spectating & Rematch ✅
- Online presence, spectator mode, rematch

## Phase 6: Polish & Anti-Cheat Hardening ✅
- Typing pattern analysis, cheat meters, toast notifications, WS reconnect

## Phase 7: Social Features ✅
- Friends list, direct challenges, custom lobbies, match chat

## Phase 8: Advanced Matchmaking ✅
- Pool-based ELO-aware matchmaker
- Dynamic ELO range widening (±100 → ±400)
- Ranked vs Unranked modes
- Season system with soft reset
- Season leaderboard and profile stats
- 23/23 tests passing

## Phase 9: Production Hardening (In Progress)
### Auth/Account — ✅ Done
- Bcrypt direct hashing
- Short-lived access tokens + long-lived refresh tokens with rotation
- Rate limiting and brute-force protection
- Strong password policy
- Password reset flow
- Change password, account deletion, logout all devices
- 35/35 tests passing

### UX Refresh — ✅ Done
- Onboarding landing page
- First-login tutorial
- Auto-connect queue with Battle button
- Glass-morphism navbar
- Removed ranked/unranked toggle from queue

### Infrastructure — Pending
- Move from SQLite to PostgreSQL
- Redis for presence, sessions, and pub/sub
- Replay system and post-game analysis
- Admin dashboard and monitoring
- Horizontal scaling for matchmaker
- DDoS protection / WAF

## Phase 10: Expansion (Future)
- Tournament system
- Clans/teams
- Practice mode vs AI
- Mobile app
- Sponsored ranked seasons
