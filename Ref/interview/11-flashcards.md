# Lesson 11 — Flashcards

Read the question, cover the answer, say the answer out loud. Repeat until automatic.

## Mental model

**Q: What is CodePandem?**
A: A real-time 1v1 competitive coding platform where two players solve the same escalating problems and see each other's progress live.

**Q: Why use WebSocket instead of HTTP polling?**
A: WebSocket is a persistent two-way connection that lets the server push state instantly. Polling adds latency and wastes resources.

**Q: What state is in-memory?**
A: Active matches, queued players, online lobby, spectators.

**Q: What state is in the database?**
A: Users, match records, friendships, refresh tokens, seasons, user season stats.

**Q: Why is the judge a separate service?**
A: So untrusted user code never runs inside the main backend, limiting the blast radius of malicious submissions.

## Config and entry

**Q: What web framework does CodePandem use?**
A: FastAPI.

**Q: Where are game constants defined?**
A: `backend/app/config.py`.

**Q: How many rounds are in a match?**
A: 3.

**Q: What are the round time limits?**
A: 180s easy, 300s medium, 480s hard.

**Q: What is the difference between `models.py` and `models_db.py`?**
A: `models.py` has in-memory dataclasses for live state; `models_db.py` has SQLAlchemy ORM models for persistence.

## Auth and security

**Q: How are passwords stored?**
A: bcrypt with 12 rounds.

**Q: How long do access tokens last?**
A: 15 minutes.

**Q: How long do refresh tokens last?**
A: 7 days.

**Q: What is refresh-token rotation?**
A: Using a refresh token invalidates it and issues a new pair, preventing token replay.

**Q: What is the login rate-limiting policy?**
A: 5 failed attempts per 15 minutes triggers a 15-minute lockout.

## Matchmaking

**Q: What algorithm pairs players?**
A: ELO-aware pool matching with widening ranges.

**Q: What is the initial ELO range?**
A: ±100.

**Q: What is the maximum ELO range?**
A: ±400.

**Q: How often does the range widen?**
A: Every 5 seconds.

**Q: What is the maximum queue wait time?**
A: 60 seconds.

## Duel lifecycle

**Q: How is the round winner determined?**
A: Highest round score; ties give no winner.

**Q: How is the match winner determined?**
A: First to 2 round wins, or best round-win count after 3 rounds, with total score as tiebreaker.

**Q: How is the submission score calculated?**
A: `base + speed * 0.01`, where `base = passed/total` and `speed = max(0, 1 - time_ms/time_limit_ms)`.

**Q: What happens when the round timer expires?**
A: `_finish_round` runs automatically and advances or ends the match.

**Q: Are ELO changes applied to unranked matches?**
A: No.

## Judge system

**Q: What is the submission timeout?**
A: 5 seconds.

**Q: What is the memory limit?**
A: 128 MB.

**Q: How many concurrent submissions can the HTTP judge handle?**
A: 4.

**Q: What uid does the judge container run as?**
A: 1000.

**Q: How is the filesystem protected in Kubernetes?**
A: `readOnlyRootFilesystem: true` with an `emptyDir` volume mounted at `/tmp`.

## Anti-cheat

**Q: Name the six anti-cheat signals.**
A: Speed, paste, tab switches, keystrokes, typing pattern, plagiarism.

**Q: What is the suspicious threshold?**
A: Composite > 0.3.

**Q: What is the flag threshold?**
A: Composite > 0.5.

**Q: Does anti-cheat prove cheating?**
A: No — it is heuristic, signaling suspicious behavior for review.

## DevOps / SRE

**Q: What are the four CI jobs?**
A: lint, test-backend, build-frontend, publish-images.

**Q: Where are images published?**
A: GHCR — `ghcr.io/sltrtn/codepandem/{backend,judge,frontend}`.

**Q: What triggers image publishing?**
A: Push to `main`, not pull requests.

**Q: What Kubernetes objects did you create?**
A: Namespace, ConfigMap, Deployments, Services, Ingress.

**Q: How did you verify self-healing?**
A: Deleted a judge pod and watched Kubernetes recreate it.

## Traps

**Q: What database is currently used?**
A: SQLite, but PostgreSQL-ready via `DATABASE_URL`.

**Q: Is there live cloud deployment?**
A: No — Kubernetes runs locally on k3d.

**Q: What is the biggest matchmaker scaling bottleneck?**
A: In-memory state; horizontal scaling needs Redis or shared state.

**Q: Say the one-liner pitch.**
A: "CodePandem is a real-time 1v1 coding duel platform with FastAPI/WebSocket, React, ELO matchmaking, anti-cheat telemetry, and an isolated non-root judge sandbox, containerized and deployed to Kubernetes with CI/CD to GHCR."
