# CodePandem — Session Handoff

## Current State
- **Version:** 0.8.0
- **Branch:** feat/redis-cache-benchmark
- **Last commit:** Bug fixes: rematch flow, custom-lobby host notification, account deletion password, round-winner text
- **Tests:** 35/35 passing
- **Frontend:** Builds clean
- **Integration Tests:** Queue matchmaking, social flow, duel chat, auth flow, and judge sandbox isolation all verified

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
10. **UX Refresh — Onboarding, Queue, Navbar** ✅
11. **Step 1 — Containerized Judge Sandbox** ✅

## What's Done Now (Step 1 — Containerized Judge Sandbox)

### Backend
- **`app/executor.py`** — shared execution core (one source of truth for local process and judge worker)
- **`app/judge.py`** — mode-aware dispatcher: `process` mode (default, tests) and `http` mode (production compose)
- **`app/judge_worker.py`** — FastAPI microservice that runs user code in the isolated judge container
- **`Dockerfile.judge`** — non-root (`judge` user) container image, concurrency semaphore, rlimit memory cap

### Infrastructure
- **`docker-compose.yml`** — added `judge` service; backend configured with `JUDGE_MODE=http` and `JUDGE_URL=http://judge:9000`
- **Isolation verified** — judge process runs as uid `1000` (non-root) and cannot read `/etc/shadow`

### Tests
- 35/35 backend tests passing (process mode default)
- Docker compose stack healthy (`backend`, `judge`, `frontend`)
- `/submit` and `/judge` endpoints work in HTTP mode

## What's Done Now (Day 2 — Docker Deep Dive, Part A)

### Infrastructure
- **`docker-compose.yml`** — added healthchecks for `backend`, `judge`, and `frontend`
- **Service startup ordering** — `backend` now waits for `judge` to be `healthy`, and `frontend` waits for `backend` to be `healthy`
- **IPv6 / localhost fix** — frontend healthcheck uses `127.0.0.1` because BusyBox `wget` resolves `localhost` to `::1` first, while nginx only listens on IPv4

### Verified
- `docker compose ps` → all three services `healthy`
- `docker inspect` shows backend health status JSON and IP address (`172.18.0.3`)
- Negative test: stopping the judge container did not break backend/frontend healthchecks; restarting the judge returned it to `healthy`
- `pytest` 35/35 passing

## What's Done Now (Day 3 — CI/CD with GitHub Actions)

### Infrastructure
- **`.github/workflows/ci.yml`** — GitHub Actions CI pipeline
  - `lint` — `ruff` code quality gate
  - `test-backend` — `pytest` (35 tests)
  - `build-frontend` — `npm ci` + `npm run build`
  - `publish-images` — builds and pushes Docker images to GHCR (only on `push` to `main`)
- **`backend/pyproject.toml`** — added minimal `[tool.ruff]` config to ignore noisy style rules (legacy code patterns like FastAPI `Depends()` defaults)

### Verified
- `ruff check app tests` passes locally
- `pytest` 35/35 passing
- Workflow triggers on `push`/`pull_request` to `main`
- GHCR packages: `ghcr.io/sltrtn/codepandem/backend`, `judge`, `frontend` published with `latest` + SHA tags

## What's Done Now (UX Refresh)
### Backend
- **`User.tutorial_completed`** boolean column added
- **`PATCH /auth/me/tutorial`** endpoint to mark tutorial complete
- **Queue WebSocket protocol** updated: `connected` on connect, `queued` after `join_queue` is sent

### Frontend
- **`OnboardingScreen`** — full-screen landing page with hero, features grid, Login/Register CTAs
- **`TutorialOverlay`** — 4-step first-login tutorial (duels, ranks, seasons, ready), calls backend to mark complete
- **QueueScreen overhaul** — auto-connects, shows "Ready for Battle" with a large Battle button, no ranked/unranked toggle (always ranked), radar animation while searching, cancel/retry support
- **Navbar overhaul** — glass-morphism (`backdrop-filter: blur`), accent brand mark, primary + secondary nav links, tier badge + avatar pill
- **App.jsx** — `/` route renders Onboarding (unauthenticated) or Tutorial (first login) or Queue (returning user)
- **AuthContext** — added `updateUser()` helper for local state mutations

### Tests
- 35/35 backend tests passing
- Frontend builds clean
- Queue matchmaking smoke test verified with new `connected` → `queued` protocol
- Social + duel smoke test verified

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

## What's Done Now (Day 4 — Kubernetes on k3d)

### Infrastructure
- **Installed** `kubectl` (v1.31.0) and `k3d` (v5.7.3) locally
- **Created** `k3d-codepandem` cluster (1 server + 2 agents) with loadbalancer port-mapped to host `8080:80`
- **`k8s/` manifests:** `namespace.yaml`, `configmap.yaml`, `backend.yaml`, `judge.yaml`, `frontend.yaml`, `ingress.yaml`
- **Reused GHCR images** from Day 3: `ghcr.io/sltrtn/codepandem/{backend,judge,frontend}:latest`
- **Judge hardening:** `runAsNonRoot: true`, `runAsUser: 1000`, `readOnlyRootFilesystem: true` with `emptyDir` mounted at `/tmp`
- **Readiness/liveness probes** on `/health` for backend, judge, frontend
- **Ingress** `codepandem.local` → frontend service; frontend nginx proxies `/api/` and `/ws/` to backend via cluster DNS

### Verified
- All pods `Running`/`Ready` across 3 nodes
- E2E judge round-trip via `/submit`: `test_cases_passed: 2, test_cases_total: 3` (sample code)
- Ingress returns frontend HTML and `/api/health` via `codepandem.local:8080`
- Self-healing: deleted judge pods recreated automatically
- Scaling: `kubectl scale deploy/judge --replicas=3` → 3 Running
- Rollout/rollback: `rollout restart`, `rollout history`, `rollout undo` all successful
- Judge pod `id` = `uid=1000(judge)`

## What's Next
- **README polish + resume update** — immediate, for application submission
- **Phase 9 (remaining): Production Hardening** — PostgreSQL, Redis, replay system, admin dashboard, horizontal scaling, DDoS protection (deferred until post-interview)

## Key Files
- Backend: `/home/mad/codepandem/backend/`
- Frontend: `/home/mad/codepandem/frontend/`
- Docker: `/home/mad/codepandem/docker-compose.yml`
- Git: https://github.com/sltrtn/CodePandem
