# CodePandem

[![CI](https://github.com/sltrtn/CodePandem/actions/workflows/ci.yml/badge.svg)](https://github.com/sltrtn/CodePandem/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-35%2F35-brightgreen)]()
[![GHCR](https://img.shields.io/badge/GHCR-images-blue)](https://github.com/sltrtn/CodePandem/pkgs/container/codepandem%2Fbackend)

Real-time 1v1 coding battles with matchmaking, ELO ratings, anti-cheat detection, and an isolated code-execution sandbox.

This repository also serves as a hands-on SRE/DevOps portfolio project: the application is containerized, health-checked, continuously delivered via GitHub Actions, and deployable to Kubernetes with self-healing, scaling, and rolling rollouts.

---

## What it does

- **Live 1v1 duels:** players are matched in real time over WebSocket, then compete to solve the same set of coding problems fastest.
- **Matchmaking + seasons:** pool-based ELO-aware matchmaker with dynamic range widening, ranked seasons, and soft reset.
- **Anti-cheat telemetry:** paste detection, tab-switch tracking, keystroke analysis, and a server-side cheat-score heuristic.
- **Isolated code execution:** user submissions run in a dedicated, non-root judge microservice with memory limits and concurrency control.
- **Social layer:** friends list, direct challenges, custom lobbies, match chat, spectator support.

## Tech stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, SQLAlchemy (SQLite/PostgreSQL-ready), WebSocket, JWT auth |
| Frontend | React + Vite, Tailwind CSS, nginx |
| Execution | Python subprocess isolation + optional HTTP judge worker |
| DevOps | Docker, Docker Compose, GitHub Actions, GHCR, Kubernetes (k3d) |

## Architecture

```
                         ┌─────────────────┐
                         │   User browser  │
                         └────────┬────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   React SPA (nginx)        │
                    │   /api/* → backend:8000    │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   FastAPI backend          │
                    │   - REST API               │
                    │   - WebSocket queue/duel   │
                    │   - Auth, ELO, seasons     │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Judge worker (non-root)  │
                    │   - uid 1000               │
                    │   - memory/concurrency cap │
                    │   - isolated execution     │
                    └────────────────────────────┘
```

## DevOps / SRE highlights

- **Container isolation:** backend, frontend, and judge each run in their own image. The judge image uses a non-root `judge` user (`uid 1000`) and a read-only root filesystem.
- **Healthchecks:** every compose service exposes a health endpoint and depends on upstream services being `healthy` before starting.
- **CI/CD:** GitHub Actions runs lint (`ruff`), 35 backend tests, frontend build, and publishes all three images to GHCR on every push to `main` — no long-lived secrets, uses scoped `GITHUB_TOKEN`.
- **Kubernetes (k3d):** manifests under `k8s/` deploy the stack to a local 3-node k3d cluster with Deployments, Services, an Ingress, readiness/liveness probes, and a ConfigMap for environment wiring. Verified behaviors: self-healing pod replacement, scaling replicas, zero-downtime rollouts/rollbacks.

## Quick start

### Local development

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v          # 35 tests
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Docker Compose

```bash
docker compose up -d
docker compose ps           # all services healthy
```

Backend: `http://localhost:8000` · Frontend: `http://localhost`

### Kubernetes (k3d)

```bash
k3d cluster create codepandem --agents 2 --port 8080:80@loadbalancer
kubectl apply -f k8s/namespace.yaml
kubectl -n codepandem apply -f k8s/
kubectl -n codepandem get pods -w
# Add to /etc/hosts: 127.0.0.1 codepandem.local
curl http://codepandem.local:8080/api/health
```

## Project structure

```
backend/             FastAPI app, tests, judge worker, Dockerfile
frontend/            React SPA, nginx config, Dockerfile
k8s/                 Kubernetes manifests
.github/workflows/   GitHub Actions CI/CD
docker-compose.yml   Multi-service local stack
```

## API overview

- `GET /health` — service status
- `GET /problems` — list problems
- `POST /submit` — submit code for a problem
- `/ws/queue` — matchmaking queue
- `/ws/duel/{match_id}` — live duel connection

## Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

35/35 backend tests pass, covering auth, matchmaking, social features, and the judge sandbox.

## Roadmap

- PostgreSQL + Redis for sessions/presence
- Replay system and post-game analysis
- Admin dashboard and observability stack
- Cloud deployment (GKE / Cloud Run) post-interview

## License

MIT
