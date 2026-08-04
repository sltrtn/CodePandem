# CodePandem — Master Document

---

## What It Is

CodePandem is a **real-time 1v1 competitive coding platform**. Two players are matched over WebSocket, then race to solve the same set of LeetCode-style problems across three escalating rounds (easy → medium → hard). The platform handles live matchmaking, ELO-based ranking, anti-cheat telemetry, spectator mode, friends, direct challenges, custom lobbies, and ranked seasons.

**The core thesis:** Most coding-practice apps are single-player. CodePandem turns coding practice into a live, social, competitive game — and then wraps the entire stack in a DevOps/SRE portfolio story (containerization, CI/CD, Kubernetes).

**Portfolio role:** SRE/DevOps credibility card with a real-time backend — covers backend engineering, WebSocket systems, security isolation, and infrastructure from one project.

**Origin story:** Evolved from earlier Android/AI projects (Meluko, ContextIQ) into a project deliberately built to demonstrate full-stack + infrastructure skills for SRE and backend roles.

---

## What Makes It Different From Every Other Coding Platform

1. **Real-time duels over WebSocket** — not just async leaderboards; players see each other's submissions live.
2. **Isolated code execution** — user submissions run in a dedicated, non-root judge microservice (uid 1000) with memory limits and concurrency control.
3. **Anti-cheat telemetry** — paste detection, tab-switch tracking, keystroke analysis, typing-pattern detection, and code-plagiarism heuristics.
4. **ELO + seasons** — competitive ranking with soft-reset seasons, not just raw scores.
5. **Social layer** — friends, direct challenges, custom lobbies, match chat, spectators.
6. **DevOps end-to-end** — Docker, Docker Compose, healthchecks, GitHub Actions CI/CD, GHCR, and Kubernetes (k3d) with self-healing and rollouts.

---

## Architecture — The Big Picture

```
Player A browser                          Player B browser
       │                                        │
       └────────┬───────────────────────────────┘
                │
    ┌───────────▼────────────┐
    │   React SPA (nginx)    │
    │   /api/* → backend     │
    │   /ws/*  → backend WS  │
    └───────────┬────────────┘
                │
    ┌───────────▼────────────┐
    │   FastAPI backend      │
    │   - REST API (auth,    │
    │     social, seasons)   │
    │   - WebSocket queue    │
    │   - WebSocket duel     │
    │   - SQLite via SQLA    │
    └───────────┬────────────┘
                │
    ┌───────────▼────────────┐
    │   Judge worker         │
    │   - uid 1000           │
    │   - 128 MB memory cap  │
    │   - concurrency 4      │
    │   - process / HTTP     │
    └────────────────────────┘
```

---

## Stack — Every Layer

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI, SQLAlchemy, SQLite (PostgreSQL-ready) | Modern async Python, easy WebSocket integration |
| Frontend | React + Vite, Tailwind CSS, nginx | SPA with fast dev build and production server |
| Real-time | WebSocket (FastAPI native) | Low-latency duel state sync |
| Code execution | Python subprocess wrapper + optional HTTP judge worker | Isolated, resource-capped execution |
| Auth | JWT (access + refresh), bcrypt | Short-lived tokens, rotated refresh tokens |
| Ranking | ELO + tier system + seasons | Standard competitive ranking |
| DevOps | Docker, Docker Compose, GitHub Actions, GHCR, Kubernetes (k3d) | Full deployment pipeline |

---

## Project Structure

```
codepandem/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point, routers, CORS
│   │   ├── config.py            # Game constants (timeouts, ELO, anti-cheat)
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models.py            # In-memory dataclasses (Match, Round, Telemetry)
│   │   ├── models_db.py         # SQLAlchemy ORM models (User, MatchRecord, etc.)
│   │   ├── auth.py              # JWT, bcrypt, refresh rotation, rate limit
│   │   ├── problems.py          # 9 hardcoded problems + selection logic
│   │   ├── scoring.py           # Submission scoring + winner determination
│   │   ├── anticheat.py         # Cheat-score heuristics
│   │   ├── executor.py          # Subprocess code runner (process mode)
│   │   ├── judge.py             # Dispatcher: process vs HTTP judge
│   │   ├── judge_worker.py      # FastAPI microservice for isolated execution
│   │   ├── matchmaking.py       # ELO-aware pool matchmaker
│   │   ├── lobby.py             # Online presence + spectators
│   │   ├── seasons.py           # Season lifecycle + soft reset
│   │   ├── routers/
│   │   │   ├── auth.py          # register/login/me/reset/delete
│   │   │   ├── health.py        # /health
│   │   │   ├── submissions.py   # /submit, /problems
│   │   │   ├── social.py        # friends, custom lobbies
│   │   │   └── seasons.py       # season stats
│   │   └── ws/
│   │       ├── queue.py         # /ws/queue
│   │       ├── duel.py          # /ws/duel/{match_id}
│   │       ├── challenge.py     # /ws/challenge
│   │       └── lobby_ws.py      # /ws/lobby
│   ├── tests/                   # 35 pytest tests
│   ├── Dockerfile               # backend image
│   ├── Dockerfile.judge         # judge image (non-root)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # screens: Queue, Duel, Profile, etc.
│   │   ├── context/             # AuthContext, DuelContext, ChallengeContext
│   │   ├── hooks/               # useWebSocket, useTelemetry
│   │   └── styles/
│   ├── Dockerfile               # multi-stage nginx image
│   └── nginx.conf               # SPA + /api proxy
├── k8s/                         # Kubernetes manifests
├── .github/workflows/ci.yml     # GitHub Actions
├── docker-compose.yml           # local multi-service stack
└── README.md
```

---

## API Contract

### REST

```
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout
POST   /auth/logout-all
POST   /auth/change-password
POST   /auth/password-reset-request
POST   /auth/password-reset
GET    /auth/me
DELETE /auth/me

GET    /problems
POST   /submit
GET    /health

GET    /social/friends
GET    /social/friends/requests
POST   /social/friends/request/{user_id}
POST   /social/friends/accept/{user_id}
POST   /social/friends/decline/{user_id}
POST   /social/friends/remove/{user_id}
POST   /social/lobby/create
POST   /social/lobby/join/{code}

GET    /seasons/current
GET    /seasons/stats
GET    /seasons/stats/{season_id}
```

### WebSocket

```
/ws/queue              # join ranked/unranked queue, receive match_found
/ws/duel/{match_id}    # submit code, chat, receive round_start/match_over
/ws/spectate/{match_id}# watch an active match
/ws/rematch/{match_id} # request a rematch after match ends
/ws/challenge          # send/accept direct challenges
/ws/lobby              # online player list + active matches
```

---

## Match Flow — Detailed

### 1. Queue
- Player opens QueueScreen; frontend connects to `/ws/queue?token=...`.
- Server authenticates via JWT query param and sends `connected`.
- Player clicks "Battle"; frontend sends `join_queue` (mode defaults to ranked).
- Matchmaker starts a background `_match_loop` that scans the pool every second.

### 2. Matchmaking
- Each queued player has an ELO and a widening range (starts at ±100, grows by ±25 every 5s, caps at ±400).
- The loop sorts players by ELO and pairs the closest two within overlapping ranges.
- On match, the loop creates a `Match` with three `Round` objects (easy, medium, hard) and assigns problems via `get_problems_for_match()`.
- Both players receive `match_found` with the `match_id`.

### 3. Duel
- Players connect to `/ws/duel/{match_id}?token=...`.
- Server sends the current `match_state` and starts the round timer (`asyncio.sleep(time_limit_s)`).
- On `submit`, code runs through `run_submission` → `judge_code` (process or HTTP mode) → `SubmissionResult`.
- Anti-cheat telemetry is evaluated and attached; round score is computed.
- Server broadcasts `duel_state` to both players and spectators.

### 4. Round / Match End
- When time expires or a player reaches `WINS_NEEDED` (2), the round or match ends.
- Winner is determined by score, then by round wins.
- For ranked matches, ELO changes are calculated and persisted.
- Match record, user stats, and season stats are written to SQLite.

---

## Judge System — Detailed

### Process mode (tests + local dev)
- `executor.py` writes user code to a temp file.
- A wrapper script sets `RLIMIT_AS` to 128 MB, runs the code, captures stdout/stderr.
- `asyncio.create_subprocess_exec` enforces a 5-second timeout.
- Output is compared line-by-line against expected output.

### HTTP mode (production / Docker / K8s)
- `judge.py` dispatches to `_judge_http` when `JUDGE_MODE=http`.
- Payload is sent to `JUDGE_URL` (e.g., `http://judge:9000/judge`).
- `judge_worker.py` is a FastAPI microservice with an `asyncio.Semaphore(4)` limiting concurrent executions.
- The judge container runs as non-root user `judge` (uid 1000) with a read-only root filesystem and an `emptyDir` volume at `/tmp`.

### Security properties
- Non-root execution (uid 1000).
- Memory cap via `setrlimit(RLIMIT_AS, 128MB)`.
- Time cap (5s).
- Concurrency cap (4 simultaneous submissions).
- Judge service is network-isolated from the backend except for the `/judge` HTTP endpoint.

---

## Anti-Cheat — Detailed

Telemetry collected on every submission:
- Paste events, paste length, burst-paste count
- Tab switches, total time outside the tab
- Keystroke count, keystrokes per second, key intervals, stddev
- Time since match start

Heuristics (`anticheat.py`):

| Check | Suspicious signal |
|---|---|
| Speed | Submission faster than difficulty threshold (8s/15s/25s) |
| Paste | Zero keystrokes + long code; paste ratio > 90%; multiple burst pastes |
| Tab switches | Multiple switches or >30s outside tab |
| Keystrokes | >15 KPS or <0.5 KPS with long code |
| Typing pattern | Low stddev (<5ms), very fast average, repeated burst intervals |
| Plagiarism | Repeated lines, hardcoded expected output in source |

Composite score = weighted sum. Thresholds: `>0.3` suspicious, `>0.5` flagged.

---

## Scoring & ELO

### Submission score
```
base  = test_cases_passed / test_cases_total
speed = max(0, 1 - time_ms / time_limit_ms)
score = base + (speed * 0.01)
```
Test cases dominate; speed is only a tiebreaker.

### Round winner
Highest round score wins; ties give no winner.

### Match winner
First to 2 round wins, or best round-win count after 3 rounds, with total score as tiebreaker.

### ELO
Standard ELO with K=32:
```
expected = 1 / (1 + 10^((opponent_elo - player_elo) / 400))
change   = K * (actual_score - expected)
```

### Tiers
- Bronze: <1200
- Silver: 1200–1599
- Gold: 1600–1999
- Platinum: 2000–2399
- Diamond: ≥2400

---

## Auth & Security

- **Password hashing:** bcrypt with 12 rounds.
- **Password policy:** ≥8 chars, uppercase, lowercase, number, special character.
- **Access tokens:** JWT, 15 minutes, type=`access`.
- **Refresh tokens:** opaque 32-byte tokens stored in DB, 7-day expiry, rotated on use (old token revoked).
- **Rate limiting:** 5 failed login attempts per 15 minutes → 15-minute lockout.
- **Account actions:** change password, delete account, logout all devices.
- **WebSocket auth:** JWT passed as query parameter.

---

## DevOps / SRE Track

| Step | What | Commit |
|---|---|---|
| Dockerization | Backend + frontend images, multi-stage nginx, compose stack | `56cedca` |
| Judge sandbox | Separate judge image, non-root uid 1000, HTTP worker mode | `882de8c` |
| Healthchecks | Service healthchecks + `service_healthy` ordering | `507eb05` |
| CI/CD | GitHub Actions: lint, 35 tests, frontend build, GHCR publish | `549606f` |
| Kubernetes | k3d cluster, Deployments/Services/Ingress, self-healing/scale/rollouts | `c7c305c` |

---

## Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

35/35 tests pass, covering:
- Auth: register, login, weak password, refresh rotation, rate limit, password reset, account deletion
- Matchmaking: queue join/leave, match creation
- Social: friend requests, custom lobbies
- Duel: round scoring, winner determination, ELO updates

---

## Build Timeline

| Days | Focus | Deliverable |
|---|---|---|
| 0–2 | Core platform: FastAPI backend, React frontend, basic judge, 9 problems | Can register, login, and run single submissions |
| 3–4 | WebSocket matchmaking + duel lifecycle | Two players can queue and duel live |
| 5–6 | Database, JWT auth, ELO | Persistent users, ranked matches, leaderboard |
| 7–8 | Profiles, leaderboard, match history | Player stats and global rankings |
| 9–10 | Lobby, spectating, rematch | Real-time presence and watchers |
| 11–12 | Anti-cheat hardening + polish | Cheat scoring, typing analysis, UI polish |
| 13–14 | Social features | Friends, direct challenges, custom lobbies |
| 15–16 | Advanced matchmaking + seasons | ELO-aware pool, dynamic range, seasons |
| 17 | Auth/account hardening | Refresh rotation, rate limiting, password reset |
| 18 | UX refresh | Onboarding, tutorial, queue overhaul, glass-morphism navbar |
| 19–21 | DevOps/SRE portfolio track | Docker, healthchecks, CI/CD, Kubernetes |

---

## Resume Bullets

**SRE / DevOps roles:**
> Built a real-time 1v1 coding duel platform (FastAPI/WebSocket + React) and containerized it into three Docker images with an isolated non-root judge sandbox (uid 1000). Implemented GitHub Actions CI/CD to GHCR and deployed to a local Kubernetes cluster (k3d) with self-healing, scaling, and zero-downtime rollouts.

**Backend roles:**
> Designed and built a real-time competitive coding backend in FastAPI with WebSocket duel state sync, ELO-based matchmaking, anti-cheat telemetry, JWT auth with refresh-token rotation, and SQLite persistence — 35 tests passing.

**Full-stack roles:**
> Built CodePandem, a React + FastAPI platform for live 1v1 coding battles, featuring matchmaking, ranked seasons, friends, direct challenges, spectator mode, and an isolated code-execution sandbox.

---

## README Headline

> *CodePandem turns coding practice into a real-time 1v1 competitive game. Two players queue up, solve the same escalating problems live, and see each other's progress in real time — all backed by ELO rankings, anti-cheat telemetry, and a non-root judge sandbox. The same stack is containerized, CI/CD-pipelined to GHCR, and deployable to Kubernetes with self-healing and rolling rollouts.*

---

## Honest Limitations (know these cold)

- **SQLite in production:** the current backend uses SQLite. It is PostgreSQL-ready via `DATABASE_URL` but not migrated yet.
- **Single-node matchmaker:** the matchmaker is an in-memory Python object. Horizontal scaling requires Redis or similar shared state.
- **No live cloud deployment:** Kubernetes runs locally on k3d; cloud deployment is planned post-interview.
- **Judge language:** currently Python-only; multi-language support would need per-language runners.
- **Anti-cheat is heuristic:** it flags suspicious behavior, not proof of cheating.

---

*Last updated: Day 4 Kubernetes complete, v0.8.0. Deep-dive study guide added: `Ref/interview/12-backend-and-devops-deep-dive.md`.*
