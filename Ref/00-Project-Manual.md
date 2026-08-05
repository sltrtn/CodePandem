# CodePandem — Project Manual

> Start here. This file explains what CodePandem is, what every major piece does, and where to find the deeper docs. It is written for someone who knows basic web development but is new to this codebase.

---

## 1. What is CodePandem?

CodePandem is a **real-time 1v1 competitive coding platform**.

In plain English: two players join a queue, get matched against each other, and race to solve the same three coding problems. Problems get harder each round (easy → medium → hard). Both players see the match state live, can chat, and spectators can watch. When the match ends, rankings change based on the standard **ELO** rating system.

The project is also a **portfolio** for SRE/DevOps/backend roles: it is containerized, has CI/CD, and is deployable to Kubernetes.

---

## 2. Three ways to run it

### A. Local development

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

cd ../frontend
npm install
npm run dev
```

- Backend runs on `http://localhost:8000`.
- Frontend runs on `http://localhost:5173`.
- Vite forwards `/api` and `/ws` to the backend automatically.

### B. Docker Compose

```bash
docker compose up --build
```

- Builds three images: `backend`, `frontend`, `judge`.
- Frontend at `http://localhost`.
- SQLite database is stored in a Docker volume, so it survives container restarts.
- The backend waits for the judge to be healthy before it starts.

### C. Kubernetes

```bash
kubectl apply -f k8s/
```

- Uses the images already published to GitHub Container Registry.
- Frontend available at `http://codepandem.local:8080`.

For exact commands, see `README.md` or `Ref/interview/09-devops-sre.md`.

---

## 3. What the app does

### Main features

| Feature | What it means |
|---|---|
| **Account system** | Register, login, change password, delete account. Passwords are bcrypt-hashed. |
| **Ranked queue** | Join a queue; get matched with someone near your ELO. |
| **Live duels** | Three rounds, real-time WebSocket state sync, live submissions, chat. |
| **Code judging** | Submitted code is run against hidden test cases inside a separate, isolated service. |
| **Anti-cheat** | Detects copy-paste, tab-switching, inhuman typing speed, and suspicious code patterns. |
| **ELO + tiers** | Win/loss changes your rating; rating determines your tier (bronze → silver → gold → platinum → diamond). |
| **Seasons** | Ranked seasons with a soft ELO reset. |
| **Social** | Friends list, friend requests, direct challenges, custom lobbies, spectators. |
| **Leaderboard** | Global ranking by ELO. |

---

## 4. The tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python + FastAPI | REST API and WebSocket server |
| Database | SQLite (PostgreSQL-ready) | Users, matches, friendships, seasons |
| Frontend | React + Vite + Tailwind CSS | The website you see |
| Real-time | WebSocket | Live duel state and lobby presence |
| Code execution | Python subprocess wrapper | Runs user code safely |
| Judge service | FastAPI microservice | Isolates untrusted code from the main backend |
| Auth | JWT + bcrypt | Short-lived access tokens, revocable refresh tokens |
| Containerization | Docker + Docker Compose | Package and run the whole stack locally |
| CI/CD | GitHub Actions | Lint, tests, frontend build, publish images to GHCR |
| Orchestration | Kubernetes (k3d locally) | Deploy, self-heal, scale, roll out updates |

---

## 5. Project folder structure

```
codepandem/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py          # App entry point, routers, CORS
│   │   ├── config.py        # Game constants (ELO, anti-cheat, etc.)
│   │   ├── database.py      # SQLAlchemy engine + sessions
│   │   ├── models.py        # In-memory data classes (Match, Round, etc.)
│   │   ├── models_db.py     # Database tables (User, MatchRecord, etc.)
│   │   ├── auth.py          # JWT, bcrypt, refresh rotation, rate limiting
│   │   ├── matchmaking.py   # The queue and match finder
│   │   ├── lobby.py         # Online presence and spectators
│   │   ├── ws/              # WebSocket endpoints (queue, duel, lobby, challenge)
│   │   ├── routers/         # REST endpoints (auth, submissions, seasons, social)
│   │   ├── executor.py      # Runs user code in a subprocess
│   │   ├── judge.py         # Chooses between local judging and HTTP judge
│   │   ├── judge_worker.py  # The separate judge microservice
│   │   ├── anticheat.py     # Cheat-score heuristics
│   │   ├── scoring.py       # How submissions are scored
│   │   └── seasons.py       # Season lifecycle and soft reset
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── Dockerfile.judge
│   └── tests/               # 35 pytest tests
├── frontend/                # React frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── context/         # Auth, duel, challenge state
│   │   ├── components/      # UI screens
│   │   └── hooks/           # useWebSocket, etc.
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.js
├── k8s/                     # Kubernetes manifests
├── docker-compose.yml       # Local multi-container setup
├── .github/workflows/       # CI/CD
├── README.md                # Project overview + quickstarts
└── Ref/                     # Study and reference docs
    ├── CodePandem_Master.md      # Master summary
    ├── interview/                 # Interview prep lessons
    │   ├── 00-roadmap.md
    │   ├── 01-mental-model.md
    │   ├── 02-config-and-entry.md
    │   ├── 03-auth-and-security.md
    │   ├── 04-matchmaking.md
    │   ├── 05-duel-lifecycle.md
    │   ├── 06-judge-system.md
    │   ├── 07-anticheat.md
    │   ├── 08-social-features.md
    │   ├── 09-devops-sre.md
    │   ├── 10-numbers-and-traps.md
    │   ├── 11-flashcards.md
    │   └── 12-backend-and-devops-deep-dive.md
    └── 00-Project-Manual.md       # This file
```

---

## 6. Core concepts explained

### 6.1 Users and authentication

- When you register, your password is hashed with **bcrypt** and stored. The server never knows your actual password.
- When you log in, you get two tokens:
  - **Access token** — a short-lived JWT (15 minutes). Used for most API/WebSocket calls.
  - **Refresh token** — a longer-lived random string stored in the database (7 days). Used only to get a new access token.
- Every time a refresh token is used, it is **revoked and replaced** with a new one. This is called refresh-token rotation.
- If you log out, the refresh token is revoked so it cannot be reused.

### 6.2 Tiers and ELO

This is the ranking system.

#### Starting point

Every new user starts at:

- **ELO: 1000**
- **Tier: bronze**
- **Highest ELO: 1000**

#### ELO formula

After a ranked match, the ELO change is calculated with the standard chess/Elo formula:

```
K = 32
expected = 1 / (1 + 10 ^ ((opponent_elo - your_elo) / 400))
actual_score = 1.0 if you won
actual_score = 0.0 if you lost
actual_score = 0.5 if draw
elo_change = round(K * (actual_score - expected), 1)
```

What this means:

- If two players have the same ELO, the winner gains +16 and the loser loses -16.
- Beating someone **much stronger** gives you a big gain.
- Losing to someone **much weaker** costs you a lot.
- Beating someone **much weaker** gives almost nothing.
- **Only ranked matches** change ELO. Unranked matches do not.

After the change is applied:

- Your current ELO is updated.
- If your new ELO is your highest ever, `highest_elo` is updated.
- Your tier is recalculated from your current ELO.

#### Tier thresholds

| Tier | ELO requirement |
|---|---|
| Bronze | below 1200 |
| Silver | 1200 |
| Gold | 1600 |
| Platinum | 2000 |
| Diamond | 2400 |

So the tier is just a label derived from your current ELO. It is updated automatically after every ranked match.

#### Match history

When a match ends, a `MatchRecord` is written to the database with:

- Both player IDs
- Winner ID
- ELO change for each player
- Number of rounds played
- Mode (ranked or unranked)
- Season ID

#### Season soft reset

A ranked season lasts 90 days by default. When a new season starts, every player's **season ELO** is pulled halfway toward 1000:

```
season_start_elo = (your_current_elo + 1000) / 2
```

Examples:

| Your ELO | New season ELO |
|---|---|
| 2000 | 1500 |
| 1400 | 1200 |
| 1000 | 1000 |

This is a **soft reset**: it keeps good players above average, gives lower players a chance to climb, but does not erase lifetime ELO. Your lifetime `elo` and `highest_elo` stay unchanged.

### 6.3 Matchmaking

1. You click **Join Queue**.
2. Your WebSocket connection to `/ws/queue` tells the backend you want to play.
3. You are placed in a pool with your ELO and chosen mode (ranked/unranked).
4. Every second, the backend scans the pool and tries to pair players whose ELOs are within each other's acceptable range.
5. The longer you wait, the wider your range grows (starts at ±100, grows by ±25 every 5 seconds, caps at ±400).
6. When a match is found, both players are told the match ID and connect to `/ws/duel/{match_id}`.

### 6.4 Duel rounds

A match has **3 rounds**:

| Round | Difficulty | Time limit |
|---|---|---|
| 1 | easy | 180 seconds (3 min) |
| 2 | medium | 300 seconds (5 min) |
| 3 | hard | 480 seconds (8 min) |

For each round:

1. Both players see the same problem.
2. They write code and submit.
3. The code is sent to the judge service.
4. The judge runs the code against hidden test cases.
5. The backend scores the result and broadcasts it to both players.
6. The round ends when the timer expires or both players have submitted.
7. The player with the higher round score wins the round.

First player to win **2 rounds** wins the match. If no one reaches 2 wins after 3 rounds, the player with the most round wins + highest total score wins.

### 6.5 How submissions are scored

For each submission:

- Base score = `test_cases_passed / test_cases_total` (correctness is most important)
- Speed bonus = up to +1% for finishing fast
- Final round score = `base + speed_bonus`

Example:

- Pass 2/3 test cases → base 0.667
- Finish in half the time → speed bonus 0.005
- Round score = 0.672

The anti-cheat system also runs and may flag suspicious behavior, but it does not change the score directly. It only marks the result as suspicious.

### 6.6 The judge (code execution)

Your submitted code does **not** run inside the main backend. It runs in a separate service called the **judge**.

Why? Because user code is untrusted. If someone submits malicious code, the blast radius should be limited.

In production mode:

1. Backend sends the code and test cases to `http://judge:9000/judge`.
2. The judge writes the code to a temporary file in `/tmp`.
3. It spawns a **subprocess** running the code with:
   - A memory limit of 128 MB (`RLIMIT_AS`)
   - A time limit of 5 seconds
4. It compares the printed output with the expected output.
5. It returns passed count, total count, time, memory, and any error.

The judge container runs as a **non-root user** with a read-only filesystem and the minimum Linux capabilities. This is a **soft sandbox**: good enough for a portfolio, but a production system would use a stronger sandbox like gVisor or Firecracker.

### 6.7 Anti-cheat

The frontend collects telemetry while you type:

- Keystrokes per second
- Number of paste events and total pasted length
- Tab switches and time spent away
- Keystroke interval variance (bots type with unnaturally regular timing)

The backend combines these into a cheat score from 0 to 1:

| Signal | What it catches |
|---|---|
| Speed | Solved too fast for the difficulty |
| Paste | Pasted long code with few/no keystrokes |
| Tab switching | Spent a lot of time outside the browser |
| Keystroke rate | Typing like a bot |
| Typing pattern | Intervals too regular |
| Plagiarism | Code contains the answer or is heavily duplicated |

A composite score above 0.3 is **suspicious**. Above 0.5 is **flagged**. This does not auto-ban anyone; it just marks the result.

### 6.8 Social features

- **Friends**: send, accept, decline friend requests.
- **Direct challenge**: challenge a friend to a match.
- **Custom lobby**: create a private lobby and invite someone.
- **Spectators**: anyone not in the match can watch a live duel over WebSocket.
- **Chat**: players can chat during a duel.

---

## 7. Backend in one paragraph

The backend is a single Python process running FastAPI on an `asyncio` event loop. It serves REST endpoints for auth, profiles, friends, seasons, and submissions. It also serves WebSocket endpoints for queueing, duels, the lobby, challenges, and spectators. All live state (queued players, active matches, online users) is stored in Python dictionaries in memory, which is why only one backend replica can run at a time. Persistent data (users, match records, friendships, tokens, seasons) is stored in SQLite.

---

## 8. Frontend in one paragraph

The frontend is a React single-page application built with Vite and styled with Tailwind CSS. It manages global state through React Context (authentication, duel state, challenge state). It talks to the backend over HTTP for API calls and over WebSocket for live updates. In development, Vite proxies `/api` and `/ws` to the backend. In production, nginx in the frontend container does the same proxying.

---

## 9. DevOps overview

| Stage | Tool | What it does |
|---|---|---|
| Containerize | Docker | Each service gets its own image with only what it needs |
| Local orchestration | Docker Compose | Runs backend, frontend, judge together with healthchecks and startup ordering |
| Code quality | ruff, pytest | Lint and 35 automated tests run in CI |
| CI/CD | GitHub Actions | On every push to `main`: lint, test, build frontend, publish images to GHCR |
| Registry | GHCR | Stores Docker images (`ghcr.io/sltrtn/codepandem/...`) |
| Orchestration | Kubernetes (k3d locally) | Deploys images with self-healing, scaling, rolling updates, and Ingress routing |

---

## 10. Common terms

| Term | Meaning |
|---|---|
| **ELO** | A numerical skill rating. Goes up when you win, down when you lose. |
| **Tier** | A label (bronze/silver/gold/platinum/diamond) derived from your ELO. |
| **JWT** | JSON Web Token. A signed token that proves who you are for a short time. |
| **WebSocket** | A persistent two-way connection between browser and server for live updates. |
| **Judge** | The service that runs submitted code against test cases. |
| **Sandbox** | An isolated environment that limits what untrusted code can do. |
| **K8s** | Short for Kubernetes. |
| **Pod** | The smallest deployable unit in Kubernetes (usually one or more containers). |
| **Deployment** | A Kubernetes object that manages a set of pods. |
| **Service** | A Kubernetes object that provides stable networking to pods. |
| **Ingress** | A Kubernetes object that routes external HTTP traffic into the cluster. |
| **ConfigMap** | Kubernetes object that stores non-secret configuration. |
| **GHCR** | GitHub Container Registry. Where Docker images are stored. |
| **CI/CD** | Continuous Integration / Continuous Deployment. Automated testing and publishing. |

---

## 11. Where to go deeper

- **Interview prep, lesson by lesson** → `Ref/interview/00-roadmap.md`
- **Master summary** → `Ref/CodePandem_Master.md`
- **Backend internals in extreme detail** → `Ref/interview/12-backend-and-devops-deep-dive.md`
- **Quick facts and honest limitations** → `Ref/interview/10-numbers-and-traps.md`
- **Drill questions** → `Ref/interview/11-flashcards.md`

---

## 12. Honest limitations

- **SQLite**: good for local/dev, but PostgreSQL would be better for production and multiple backend replicas.
- **Single backend replica**: matchmaker state lives in memory. Scaling out requires Redis or a shared matchmaking service.
- **No live cloud deployment**: Kubernetes runs locally on k3d.
- **Python-only judge**: the code runner currently only supports Python.
- **Soft sandbox**: the judge is isolated but not hardened against a determined attacker.
- **Blocking DB calls in WebSocket handlers**: sync SQLAlchemy queries briefly block the async event loop.

These are all valid "what would you improve next?" answers in an interview.
