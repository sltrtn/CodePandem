# CodePandem — Session Handoff

## Current State
- **Version:** 0.6.0
- **Branch:** main
- **Last commit:** Phase 9 auth/account hardening complete
- **Tests:** 35/35 passing
- **Frontend:** Builds clean
- **Integration Tests:** Queue matchmaking, social flow, duel chat, and auth flow all verified

## Completed Phases
1. **Phase 1:** Core platform
2. **Phase 2:** WebSocket integration
3. **Phase 3:** Database & Auth
4. **Phase 4:** Profiles, Leaderboard, Easter Egg
5. **Phase 5:** Lobby, Spectating, Rematch
6. **Phase 6:** Polish & Anti-Cheat Hardening
7. **Phase 7:** Social Features
8. **Phase 8:** Advanced Matchmaking
9. **Phase 9 — Auth/Account Hardening** ✅

## What's Done Now (Phase 9 — Auth/Account)
### Backend
- **Bcrypt direct** — replaced passlib with direct `bcrypt` hashing to eliminate version warnings
- **Short-lived access tokens** — 15-minute JWT access tokens
- **Long-lived refresh tokens** — 7-day opaque refresh tokens with rotation (old token invalidated on refresh)
- **Rate limiting / brute-force protection** — 5 failed login attempts per 15 minutes, then 15-minute lockout
- **Strong password policy** — minimum 8 chars, uppercase, lowercase, number, special character
- **Password reset tokens** — time-limited reset tokens with `/auth/password-reset-request` and `/auth/password-reset`
- **Change password** — `/auth/change-password` with current password verification
- **Account deletion** — `/auth/me` DELETE with password verification
- **Logout all devices** — `/auth/logout-all` revokes all refresh tokens

### Frontend
- **AuthContext** — access/refresh token storage, automatic refresh, `logoutAll`, `changePassword`, `requestPasswordReset`, `confirmPasswordReset`, `deleteAccount`, `apiRequest`
- **LoginScreen** — password reset request flow
- **RegisterScreen** — live password requirement feedback
- **ProfileScreen** — change password, logout all devices, delete account
- **ResetPasswordScreen** — `/reset-password?token=...` confirmation page

### Tests
- 35/35 backend tests passing
- 12 new auth tests: register/login, weak password, invalid password, refresh rotation, rate limit, password reset, duplicate username, account deletion, change password, logout all, token expiry
- Smoke tests: queue matchmaking, social + duel flow, auth flow

## Known Non-Blocking Issues
- (none)

## What's Done Now (Dockerization)
- **`backend/Dockerfile`** — Python 3.14-slim, `pip install`, exposes 8000
- **`frontend/Dockerfile`** — multi-stage: Node 26 build → nginx:alpine serve
- **`frontend/nginx.conf`** — SPA routing (`try_files` fallback)
- **`docker-compose.yml`** — backend + frontend services, named volume for SQLite, env vars for CORS/JWT/DB
- **Configurable DB** — `DATABASE_URL` env var, defaults to `sqlite:///./codepandem.db`
- **Configurable CORS** — `CORS_ORIGINS` env var with sensible defaults
- **Cleanup** — removed unused `passlib[bcrypt]` and `bcrypt<4.1` pin from requirements

Usage: `docker compose up` (add `-d` for detached). Runs on ports 8000 (API) and 80 (frontend).

## What's Next
- **Phase 9 (remaining): Production Hardening** — PostgreSQL, Redis, replay system, admin dashboard, horizontal scaling, DDoS protection

## Key Files
- Backend: `/home/mad/codepandem/backend/`
- Frontend: `/home/mad/codepandem/frontend/`
- Docker: `/home/mad/codepandem/docker-compose.yml`
- Git: https://github.com/sltrtn/CodePandem
