# CodePandem — Interview Prep Roadmap

> Study guide series. Read in order. Each file is one lesson. Every concept is mapped to your actual code.

## The goal

You can explain CodePandem from first principles, trace a duel request through the backend, and defend every architectural decision in an interview.

## Learning formats

| Format | Where |
|---|---|
| Written lessons | These `.md` files |
| Master overview | `Ref/CodePandem_Master.md` |
| Interactive Q&A | Live chat sessions |
| Flashcards | `11-flashcards.md` |
| Mock interviews | Live chat rounds |

## The sequence

- [ ] **00 — Roadmap** (this file)
- [ ] **01 — Mental model** — what CodePandem is, WebSocket vs HTTP, real-time duel flow
- [ ] **02 — Config and entry** — `main.py`, `config.py`, models
- [ ] **03 — Auth and security** — JWT, refresh rotation, rate limiting, password policy
- [ ] **04 — Matchmaking** — ELO-aware pool, range widening, pairing algorithm
- [ ] **05 — Duel lifecycle** — queue → match → duel → scoring → persist
- [ ] **06 — Judge system** — `executor.py`, `judge_worker.py`, isolation, security
- [ ] **07 — Anti-cheat** — telemetry collection and cheat-score heuristics
- [ ] **08 — Social features** — friends, direct challenges, custom lobbies, spectators
- [ ] **09 — DevOps / SRE** — Docker, healthchecks, CI/CD, Kubernetes
- [ ] **10 — Numbers and traps** — quick facts + honest limitations
- [ ] **11 — Flashcards** — Q&A drills

## How to use this

1. Read one file.
2. Close it and explain the concept out loud.
3. Open the referenced code file and trace the actual lines.
4. Try the self-check questions without looking.
5. Move on only when you can answer in plain English.

## The one rule

Every answer must connect to **your code**. Abstract definitions alone won't survive an interview follow-up.
