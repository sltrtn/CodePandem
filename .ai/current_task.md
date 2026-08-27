# Current Task

> Always represents exactly what is currently being worked on.

---

## Objective

Fix critical UI/gameplay bugs discovered in the full codebase audit and prepare the `feat/redis-cache-benchmark` branch for Redis/performance work.

---

## Status

Critical bug-fix pass complete. All 35 backend tests pass, frontend builds clean, `ruff` clean.

---

## Recently Completed

- [x] Fix duel round-winner text (now correctly shows You/Opponent/Draw)
- [x] Fix account deletion flow (frontend now prompts for and sends password)
- [x] Fix custom-lobby host notification (host is pushed the match_id and navigates)
- [x] Fix rematch system (new match is created and both players navigate to it)
- [x] Keep finished matches in memory briefly for rematch, with safe `_player_match` cleanup
- [x] Update `.ai/handoff.md` current state

---

## Known Remaining Gaps

See full audit for details. Highest priority after this pass:

- [ ] Wire Redis caching into the backend (leaderboard/problems)
- [ ] Add PostgreSQL service to Docker Compose
- [ ] Add frontend tests / integration tests
- [ ] Fix spectator code panels (currently empty)
- [ ] Fix `useTelemetry` reset and tab-switch tracking
- [ ] Protect admin endpoints and remove dev-mode password-reset token leak

---

## Next Immediate Step

Continue with Redis/performance branch wiring or scaffold the separate Go 1M-RPS benchmark repo.
