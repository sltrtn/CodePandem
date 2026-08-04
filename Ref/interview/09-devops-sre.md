# Lesson 9 — DevOps / SRE: Docker, CI/CD, and Kubernetes

## What this lesson covers

- Docker + Compose setup
- Healthchecks and startup ordering
- GitHub Actions CI/CD
- Kubernetes manifests and verified behaviors

## Docker Compose

File: `docker-compose.yml`

Services:
- `backend` — FastAPI on port 8000
- `judge` — judge worker on port 9000, `JUDGE_MODE=http`
- `frontend` — nginx on port 80

The backend depends on judge being healthy before it starts. The frontend depends on backend.

```yaml
services:
  backend:
    build: ./backend
    environment:
      JUDGE_MODE: http
      JUDGE_URL: http://judge:9000
    depends_on:
      judge:
        condition: service_healthy
```

## Healthchecks

Each service has a healthcheck endpoint:
- backend: `GET /health`
- judge: `GET /health`
- frontend: `wget --spider http://127.0.0.1/`

`127.0.0.1` is used for the frontend because BusyBox `wget` resolves `localhost` to IPv6 first while nginx listens on IPv4.

## CI/CD

File: `.github/workflows/ci.yml`

Jobs:
1. `lint` — `ruff check app tests`
2. `test-backend` — `pytest` (35 tests)
3. `build-frontend` — `npm ci && npm run build`
4. `publish-images` — build and push backend/judge/frontend to GHCR

Publish runs only on `push` to `main`, not on pull requests. It uses the scoped `GITHUB_TOKEN`.

## Kubernetes

Files: `k8s/*.yaml`

- `namespace.yaml` — `codepandem` namespace
- `configmap.yaml` — `JUDGE_MODE`, `JUDGE_URL`, `CORS_ORIGINS`
- `backend.yaml` — Deployment + Service
- `judge.yaml` — Deployment + Service with non-root securityContext
- `frontend.yaml` — Deployment + Service
- `ingress.yaml` — Ingress routing `codepandem.local` to frontend

Verified behaviors:
- E2E submission through cluster: success
- Self-healing: deleted pods recreated
- Scaling: `kubectl scale deploy/judge --replicas=3`
- Rollout/rollback: `rollout restart`, `rollout history`, `rollout undo`
- Non-root judge: `uid=1000(judge)`

## Why this matters in an interview

You can say:

> "The stack is fully containerized: backend, judge, and frontend each have their own image. Docker Compose adds healthchecks and startup ordering. GitHub Actions runs lint, 35 tests, frontend build, and publishes all images to GHCR on every push to main using a scoped token. For Kubernetes, I deployed the same images to a local k3d cluster with Deployments, Services, an Ingress, readiness probes, and a non-root judge pod. I demonstrated self-healing, scaling, and zero-downtime rollouts."

## Common trap

**"Is this running in production on the cloud?"**

Honest answer: not yet. Kubernetes runs locally on k3d. The README and CI pipeline are production-shaped, but live cloud deployment is planned post-interview. This is still strong for a fresher because it shows you understand the entire pipeline.

## Self-check

1. What are the three Docker Compose services?
2. How does the backend know where the judge is in Compose?
3. What are the four CI jobs?
4. Why does publish-images only run on push?
5. What Kubernetes objects did you create?
6. How did you verify self-healing?

## Code map

| Concept | File |
|---|---|
| Compose stack | `docker-compose.yml` |
| CI/CD | `.github/workflows/ci.yml` |
| K8s manifests | `k8s/*.yaml` |
| Judge Dockerfile | `backend/Dockerfile.judge` |
| Backend Dockerfile | `backend/Dockerfile` |
| Frontend Dockerfile | `frontend/Dockerfile` |
