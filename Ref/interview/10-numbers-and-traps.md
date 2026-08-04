# Lesson 10 — Numbers and Traps

## Quick-reference numbers

| Fact | Value |
|---|---|
| Backend tests passing | 35/35 |
| Problems | 9 (3 easy, 3 medium, 3 hard) |
| Rounds per match | 3 |
| Round time limits | 180s (easy), 300s (medium), 480s (hard) |
| Wins needed to win match | 2 |
| Submission timeout | 5 seconds |
| Memory limit | 128 MB |
| Judge concurrency | 4 |
| Judge user uid | 1000 |
| ELO K-factor | 32 |
| Matchmaking initial range | ±100 ELO |
| Matchmaking max range | ±400 ELO |
| Matchmaking max wait | 60 seconds |
| Access token expiry | 15 minutes |
| Refresh token expiry | 7 days |
| Login rate limit | 5 failed attempts / 15 min → 15 min lockout |
| Anti-cheat warn threshold | 0.3 |
| Anti-cheat flag threshold | 0.5 |
| Season duration | 90 days |

## Honest limitations to know cold

1. **SQLite in production**
   - Current DB is SQLite via `DATABASE_URL` default.
   - PostgreSQL-ready by changing `DATABASE_URL`.
   - Not yet migrated or tuned.

2. **Single-node matchmaker**
   - The matchmaker is a Python object in one process.
   - Horizontal scaling requires Redis or another shared state store.

3. **No live cloud deployment**
   - Kubernetes runs on local k3d.
   - Cloud deployment is planned, not executed.

4. **Python-only judge**
   - Submissions must be Python.
   - Multi-language support would need separate runners.

5. **Anti-cheat is heuristic**
   - Flags suspicious behavior, not proof of cheating.
   - No human review workflow yet.

6. **In-memory matches are lost on restart**
   - Active matches disappear if the backend restarts.
   - Match records are persisted only after completion.

## Common interview traps and strong answers

**"How do you scale this?"**
- Move matchmaker state to Redis.
- Replace SQLite with PostgreSQL.
- Run multiple backend replicas behind a load balancer with sticky WebSocket sessions.
- Deploy judge workers as a separate horizontally scalable service.

**"Is the judge fully secure?"**
- It is a strong isolation layer but not a full sandbox.
- For production untrusted code, add seccomp/gVisor/VM per submission.
- Current design demonstrates security thinking at the right scope.

**"Why k3d and not a real cloud cluster?"**
- k3d gives a real Kubernetes API locally with zero cost.
- All manifests and behaviors are transferable to EKS/GKE/AKS.
- Cloud deployment is the next step, not a prerequisite for learning.

## The one-liner pitch

> "CodePandem is a real-time 1v1 coding duel platform. It has FastAPI/WebSocket backend, React frontend, ELO matchmaking, anti-cheat telemetry, and an isolated non-root judge sandbox. The whole stack is containerized, tested with 35 backend tests, continuously delivered via GitHub Actions to GHCR, and deployed to a local Kubernetes cluster with self-healing and rolling rollouts."

## Self-check

1. Recite the key numbers without looking.
2. What are the three biggest honest limitations?
3. How would you scale the matchmaker?
4. How would you make the judge fully secure?
5. Say the one-liner pitch out loud.
