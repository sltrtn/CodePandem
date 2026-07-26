# Current Task

> Always represents exactly what is currently being worked on.

---

## Objective

Build a full social competitive platform. Phase 4 (Profiles, Leaderboard & Easter Egg) is complete. Next: Phase 5 (Lobby & Spectating).

---

## Status

Phase 4 complete. Profiles, leaderboard, match history, and Slater Easter egg all working. Ready for Phase 5.

---

## Steps

- [x] Backend scaffold (FastAPI, WebSocket, models, config)
- [x] Judge (subprocess execution, stdin piping, memory limit, timeout)
- [x] Scoring (tiered: test cases primary, speed tiebreaker)
- [x] Anti-cheat (paste, tab switch, keystroke, speed analysis)
- [x] Matchmaking (asyncio.Queue + Futures pairing)
- [x] Queue WebSocket handler
- [x] Duel WebSocket handler (submit, broadcast, timer)
- [x] Frontend scaffold (React + Vite + routing)
- [x] QueueScreen, DuelScreen, CodeEditor, Scoreboard, ResultsScreen
- [x] Dark theme CSS
- [x] Backend tests (19 passing)
- [x] WebSocket integration (CONNECTED case fix, player_id fix, UUID fix)
- [x] DuelContext localStorage fix
- [x] Round.winner field + serialization
- [x] SQLite + SQLAlchemy database
- [x] User model + MatchRecord model
- [x] JWT authentication (register, login, me)
- [x] WebSocket authentication (token query param)
- [x] ELO rating system + tier badges
- [x] Frontend auth (AuthContext, LoginScreen, RegisterScreen)
- [x] Protected routes
- [x] Player profile page (stats grid, match history)
- [x] Global leaderboard page (sorted by ELO)
- [x] Match history display (per player, with ELO changes)
- [x] Frontend navigation (navbar)
- [x] Slater Easter egg (tap username 7 times)
- [ ] Online players in lobby
- [ ] Spectate active matches
- [ ] Rematch system

---

## Next Immediate Step

Phase 5: Lobby — show online players, spectate active matches, rematch system.
