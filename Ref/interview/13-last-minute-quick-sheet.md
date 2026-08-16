# CodePandem — Interview Quick Sheet (Last-Minute Revision)

> The 20% that produces 80% of the questions. Memorize Section A cold. Skim the rest. Always bring answers back to YOUR code and name the FILE.

---

## SECTION A — The 6 questions you MUST nail

### 1. "Tell me about your project." (Guaranteed. 90% of the interview hinges on it.)

> "I built **CodePandem**, a real-time competitive coding arena — 1v1 duels where two players get the same problem, race a shared timer, and submit through an online judge that I built myself. The insight: existing platforms (LeetCode, Codeforces) are single-player or contest-based — nobody does **head-to-head, live, WebSocket-driven** duels with skill-based matchmaking. So I built the whole thing end-to-end: **FastAPI backend**, **React/Vite frontend**, a **sandboxed judge service** that executes and scores code safely, **JWT auth** with refresh rotation, **ELO matchmaking** with range widening, **anti-cheat** telemetry, **seasons** with soft rating resets, and **real-time sync** for duels, lobbies, and spectating. Deployed with **Docker Compose**, orchestration manifests for **Kubernetes**, and a **GitHub Actions CI pipeline** that lints, tests, and builds images."

### 2. "What was the biggest technical challenge?" / "What was hard?"

Pick the ones that map to the interviewer's vibe (SRE/DevOps → A & C, backend → B, product → D):

**A. Running untrusted code safely (the judge).**
> "The judge has to execute arbitrary user submissions and not let them crash the platform or steal secrets. I run each submission in an **isolated subprocess with hard resource limits** — `RLIMIT_AS` caps memory, a hard `timeout_s` kills runaway loops — so a `while True` or a `malloc` bomb gets killed instead of taking down the service. The judge is also a **separate container** (`Dockerfile.judge`) from the API, so a bad submission can't touch the app or the database."

**B. Real-time duel state over WebSockets.**
> "A duel is a state machine — queue → round_active → results. Both players, the judge result, the timer, and spectators all need to see the same state **within milliseconds**. I built the whole lifecycle in `backend/app/ws/duel.py` (555 lines): each match is an in-memory `Match` object, state transitions are broadcast over WebSocket, and the judge verdict is delivered live so both sides see 'Accepted' the instant it happens — no polling."

**C. Matchmaking that's fair AND fast.**
> "The tension: a strict ±100 ELO window gives fair matches but long waits — and in a small queue, infinite waits. I solved it with **range widening**: a player starts wanting opponents within ±100 ELO, and that window grows by ±25 every 5 seconds up to a ±400 cap (`matchmaking.py:169-175`). If no fair opponent shows up, the system *gradually* accepts wider ones instead of stalling. Players are capped at 60s in queue, then removed. It's the same trick every game (Dota, League, chess) uses — and I tuned the constants myself."

**D. Anti-cheat that respects the product.**
> "If it's a duel, cheating is fatal. I capture **client telemetry** — keystrokes, paste events, tab switches — and score it (`anticheat.py`): pasting a full solution in under 5s, 0 keystrokes with a long submission, or 3+ tab switches all flag. Each signal is weighted (speed ≤ 1.0, paste ≤ 0.9, tab ≤ 0.3) and summed; over 0.5 flags the match. It's honest: a normal fast solve stays under the threshold."

### 3. "Why did you use X technology?" (table covers all of them)

| Tech | Why (one-liner) |
|---|---|
| FastAPI | Async native — perfect for WebSocket duels + per-request DB via SQLAlchemy; typed, auto-docs |
| Python | Best language for the judge subprocess + resource-limit control via `resource` |
| PostgreSQL | Relational, transactional — correct for users/matches/seasons with real relations |
| SQLAlchemy | ORM with typed models (`models_db.py`), single source of truth for the schema |
| React 19 + Vite | Fast dev, componentized UI, state via React Context for real-time updates |
| WebSockets | Push state to both players + spectators with ~no latency; the core of a duel |
| JWT (python-jose) | Stateless auth; 15-min access + 7-day refresh tokens, refresh rotation |
| Docker Compose | Local dev parity with prod: backend/frontend/judge/db as services with healthchecks |
| Kubernetes (k3d) | Orchestration practice + the reason I understand probes, services, ingress |
| GitHub Actions | CI: ruff lint + pytest on the backend, builds images |
| GHCR | Publically-pullable images so K8s manifests deploy from the registry, not local |

### 4. "What is your role in the project?"

> "I designed and built the entire system end-to-end — architecture, data model, auth, judge sandbox, matchmaking, ELO/seasons, anti-cheat, frontend, CI/CD, Docker, and K8s manifests. I made every architectural decision and can defend each one, from 'why subprocess for the judge' to 'why range widening over a flat window'."

### 5. "What is the one-line pitch / what does it do?"

> "CodePandem is a real-time 1v1 competitive coding arena — you queue up, get matched by skill, and race an opponent on the same problem with a live judge and a shared timer."

### 6. "What would you improve / what's next?"

> "Three things: (1) **more test coverage** — I have pytest for backend logic but want property-based tests on the ELO/season math and integration tests on the duel state machine; (2) **external judge backends** — pull problems from Codeforces/LeetCode like CPDuels does, instead of only my bundled problem set; (3) **persistent match history UI** and a richer leaderboard. Also **rate limiting on auth endpoints** and moving the in-memory match store to Redis so I can scale to multiple API replicas." — Honest limitations + a concrete scale path. Interviewers love this.

---

## SECTION B — Backend / system fundamentals (very likely asked)

**Q: FastAPI vs Flask/Django?**
A: FastAPI is async-first — coroutine-based WebSocket handling is a first-class feature, which a real-time duel platform needs. It's also typed with Pydantic, so request/response validation is automatic and the OpenAPI docs are generated. Flask is sync; Django is heavier and sync-first.

**Q: What is a WebSocket? How is it different from HTTP?**
A: HTTP is request/response — the client asks, the server answers. A WebSocket is a **persistent, bidirectional** connection over a single TCP socket. The server can push to the client at any time — that's how I broadcast duel state (round start, verdicts, results) to both players and spectators without polling.

**Q: JWT — how does it work?**
A: Three parts: **header** (algorithm), **payload** (claims: user id, token type, exp), **signature** (HMAC with a secret). The server signs it; clients send it; the server verifies the signature + expiry. Stateless — no session store. Mine: access token 15 min, refresh token 7 days (`auth.py:19-20`). On expiry the client hits `/auth/refresh` with the refresh token to get a new access token.

**Q: Why both access AND refresh tokens?**
A: Short-lived access tokens limit damage if one leaks (15 min). The refresh token (longer, stored safely) is the only thing that can mint new ones. Trade-off: access stays stateless/fast, refresh gives continuity without a session DB.

**Q: How does the judge execute code?**
A: Writes the user's code to a temp file, runs it in a **subprocess** with `resource.setrlimit(RLIMIT_AS, ...)` to cap memory and a hard `timeout_s` for wall-clock time (`executor.py`). Feeds test input on stdin, captures stdout, compares to expected. Runs in a **separate judge container** so it's isolated from the API.

**Q: What is a subprocess? Why subprocess for the judge?**
A: A separate OS process — the kernel isolates it. If user code `os._exit(0)`s or segfaults, only that process dies; the API stays up. Combined with rlimits, it's OS-level sandboxing without needing a full VM per submission.

**Q: SQL vs NoSQL — why Postgres?**
A: My data is **relational** — users, matches, match players, seasons, ELO histories with FKs and aggregates (leaderboards). SQL gives transactions (a match + both ELO updates must commit together) and joins. NoSQL would've been a fight against the grain. (Note: Meluko's Firestore was the right call *there* — real-time listeners — but that's the wrong tool here.)

**Q: What is ELO / how is it calculated?**
A: A skill rating that updates by the **gap between the expected result and the actual result**. `expected = 1 / (1 + 10^((opp_elo − my_elo)/400))`; `change = K × (score − expected)` with K=32 (`ws/duel.py:265-287`). Win vs. a much-stronger player = big gain; win vs. much-weaker = tiny gain. The two players' changes are symmetric, so total rating is conserved.

**Q: What is a tier?**
A: A discrete band over ELO (`models_db.py:44-54`): bronze < 1200, silver 1200, gold 1600, platinum 2000, diamond 2400. Nice for the UI; ELO is the continuous truth underneath.

**Q: What is a season and the soft reset?**
A: Every 90 days a new season (`seasons.py`). ELO gets a **soft reset** — `(elo + 1000) / 2` — not wiped. A 2000 player starts next season at 1500, not 1000. Incentivizes grinding without punishing prior skill. Each season tracks `season_elo` and `highest_season_elo`.

**Q: What is range widening in matchmaking?**
A: Each queued player accepts opponents within a window that starts at ±100 ELO and grows by +25 every 5s up to ±400, with a 60s max wait (`matchmaking.py:169-175`, `config.py:23-27`). Fair when possible, fast when not. Constants are config-driven so I can tune them per population.

**Q: What is a health check / why do containers need them?**
A: `/health` endpoints let the orchestrator (Compose or K8s) know a container is alive. The judge and backend expose `/health`; Compose uses them as `healthcheck`; in K8s they'd be `livenessProbe`/`readinessProbe` — liveness restarts dead containers, readiness stops sending traffic to not-yet-ready ones.

**Q: What is CI/CD?**
A: CI = automatically lint + test every push (my GitHub Actions runs ruff + pytest on the backend). CD = automatically build and ship. My pipeline builds Docker images and pushes them to GHCR; the K8s manifests pull from there.

**Q: Docker image vs container?**
A: An image is the **blueprint** (read-only snapshot: code, deps, config). A container is a **running instance** of that image. I build multi-stage: `node:alpine` builds the frontend, `nginx:alpine` serves the static output — so the shipped image is small and doesn't carry build tools.

---

## SECTION C — Your design decisions (they'll probe here)

**Q: "Why a separate judge container?"**
A: "Failure isolation + resource isolation. User code is untrusted — it can crash, spin forever, or gobble memory. Running it in its own service means a hostile submission can only hurt the judge, never the API, the DB, or other matches. It also lets me scale the judge independently if load grows."

**Q: "Why is the match state in memory, not the DB?"**
A: "A live duel is microseconds-sensitive — the timer, the round state, both sockets. Writing every tick to Postgres would add latency and DB load. In-memory (`matchmaking.py` `_matches`) gives instant reads/writes; only **outcomes** are persisted (Match record + ELO changes). The trade-off: state doesn't survive a backend restart — the honest fix at scale is Redis."

**Q: "How do you stop someone cheating?"**
A: "Three layers. (1) **Judge** — code is executed against hidden test cases, so you can't fake an AC. (2) **Anti-cheat telemetry** — keystrokes, paste events, tab switches are scored and a high score flags the match (`anticheat.py`). (3) **Honest answer**: like any platform, a determined cheater can always find an angle — the scoring is a deterrent, not a wall, and I'd add pattern-similarity checks across submissions next."

**Q: "How would you scale this to 10,000 users?"**
A: "The DB and judge already scale horizontally (Postgres + stateless judge). I'd: (1) move in-memory match state + matchmaker to **Redis** so multiple backend replicas share one queue, (2) put a **load balancer / ingress** in front (my K8s ingress manifest is already drafted), (3) run N judge replicas behind a work queue, (4) add **rate limiting** on auth + submission endpoints, and (5) cache the leaderboard query instead of recomputing."

**Q: "Why did you choose this architecture?"**
A: "Three services with a clear ownership boundary — API (FastAPI) for everything business logic, Judge for execution, frontend (nginx) for static serving — over one Postgres. WebSockets for real-time, JWT for stateless auth, in-memory for live state, Postgres for truth. It's the smallest architecture that's still production-shaped, and every piece has a replacement path at scale (Redis, more judges, ingress)."

**Q: "Why SQLAlchemy / an ORM?"**
A: "Typed Python models (`models_db.py`) that map to real tables — `User`, `Match`, `Season`, `SeasonMembership`. One place defines the schema; the app never writes raw SQL strings. FKs between matches and users make leaderboard queries and history joins trivial."

---

## SECTION D — Frontend (likely asked, keep short)

**Q: React state vs Context vs external store?**
A: I used **Context + hooks** (`AuthContext`, `DuelContext`, `ChallengeContext`) — right-sized for this app. The duel screen pulls live state from the WebSocket into context and renders components off it. No Redux — unnecessary weight for two real-time screens.

**Q: How does the frontend talk to the backend?**
A: REST for auth/social/leaderboard (axios), **WebSocket** for queue, duel, lobby, and spectate. The WS URL is built from `window.location.host`, so the same build works on localhost, a LAN IP, or behind a domain with zero hardcoded URLs.

**Q: How do you handle a failed request?**
A: Axios interceptor checks for 401; on a stale access token it silently calls `/auth/refresh`, retries the original request, and only logs the user out if refresh fails. The boot session check validates the stored token against `/auth/me` so a dead session never wedges the app.

**Q: How did you handle the stuck 'Judging...' button?**
A: A classic state bug — `submitting` was set true but never reset. Fixed by deriving the button state from `lastSubmission` in a `useEffect`, so it resets the moment a verdict arrives. Good example of why you keep UI state in sync with the event lifecycle, not a one-way flag.

---

## SECTION E — Behavioral (almost always asked)

**Q: Tell me about yourself.**
A: "I'm a CS student who builds full systems end-to-end. Two flagship projects: **Meluko**, a native Android social alarm clock (Kotlin/Compose/Firebase, shipped signed release APK) built around system reliability — exact alarms, Doze, offline — and **CodePandem**, a real-time 1v1 coding arena where I built the judge, matchmaking, and real-time sync from scratch, containerized and CI/CD'd. I like measurable engineering: Meluko is reliability-focused, CodePandem is latency- and fairness-focused."

**Q: Why this role?** (adapt to Saviynt SRE JD)
A: "The JD asks for CI/CD, Docker, Kubernetes, scripting, Git, and production troubleshooting — that's literally what CodePandem is built on. And it's an IAM/security company: I care about identity and least privilege — my auth design (short-lived tokens, refresh rotation, security-minded rules) shows I think about security by default, not as an afterthought."

**Q: What's your strength?**
A: "End-to-end ownership — I go from schema to UI to a deployed, CI-checked, containerized system, and I can defend every architectural decision with the trade-off I weighed."

**Q: What's a weakness?**
A: "I still write tests more often after the feature than before it. CodePandem has pytest coverage for backend logic but I'd like TDD discipline and more property-based tests on the ELO and season math. It's something I'm actively fixing."

**Q: How do you handle conflict / a disagreement?**
A: "I listen first, then bring data. When I chose range widening over a fixed ELO window, I could justify it with the small-queue problem it solves. If someone shows me better data, I change — the constants are config-driven specifically so tuning is easy."

**Q: Where do you see yourself in 5 years?**
A: "Growing from a developer into a senior/lead engineer — owning distributed systems end-to-end, mentoring juniors, and leading architecture decisions for a product team."

---

## SECTION F — "Do you know anything we didn't cover?" (last question — always say yes)

Offer one of these briefly:
- The judge sandbox: how rlimits + subprocess + a separate container stop malicious code
- Range widening: the fairness-vs-queue-time trade-off in one formula
- ELO/season math: why soft reset `(elo + 1000)/2` and K=32
- The duel state machine: queue → rounds → verdicts → ELO, all over one WebSocket
- Anti-cheat scoring from client telemetry
- CI: ruff + pytest in Actions → images to GHCR → K8s pulls from registry

---

## Rapid-fire recall (say these out loud before bed)

1. CodePandem = real-time 1v1 coding duels: same problem, shared timer, live judge.
2. Stack: FastAPI + React/Vite + Postgres/SQLAlchemy + WebSockets + JWT + Docker + K8s + GH Actions.
3. Judge = subprocess + `RLIMIT_AS` memory cap + `timeout_s` + separate judge container.
4. Matchmaking = range widening: ±100 → +25/5s → ±400 cap; 60s max wait.
5. ELO = `expected = 1/(1+10^((Δ)/400))`, `change = K(score−expected)`, K=32, symmetric.
6. Tiers: bronze <1200 < silver <1600 < gold <2000 < platinum <2400 < diamond.
7. Seasons = 90 days, soft reset `(elo + 1000)/2`, tracks highest season ELO.
8. Auth = JWT, 15-min access + 7-day refresh, rotation on refresh; stateless.
9. Real-time = WebSockets in `ws/duel.py`; state machine broadcast to both players + spectators.
10. Anti-cheat = telemetry (keystrokes/paste/tab) scored; > 0.5 flags the match.
11. Deploy = Compose (backend/frontend/judge/db) + k3d K8s manifests + CI lints/tests/builds.
12. Health checks = `/health` on backend + judge; K8s liveness/readiness.

**Final tip:** For every answer, name the FILE (`ws/duel.py`, `matchmaking.py`, `judge_worker.py`, `anticheat.py`, `models_db.py`, `seasons.py`, `auth.py`, `docker-compose.yml`, `.github/workflows/ci.yml`). It sounds like you own the code — because you do.
