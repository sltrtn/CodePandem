# Lesson 2 — Config and Entry: How the Backend Starts

## What this lesson covers

- How the FastAPI app starts (`main.py`)
- Where game constants live (`config.py`)
- The difference between in-memory models and database models

## FastAPI entry point

File: `backend/app/main.py`

```python
app = FastAPI(title="CodePandem", version="0.8.0")

origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost",
).split(",")

app.add_middleware(CORSMiddleware, ...)

app.include_router(health.router)
app.include_router(submissions.router)
app.include_router(auth.router)
app.include_router(social.router)
app.include_router(seasons.router)
app.include_router(queue.router)
app.include_router(duel.router)
app.include_router(lobby_ws.router)
app.include_router(challenge.router)

@app.on_event("startup")
def on_startup():
    init_db()
    get_current_season()
```

What this means:
- CodePandem is a FastAPI server.
- It has REST routers and WebSocket routers.
- CORS origins are configurable via environment variable.
- On startup it creates DB tables and ensures an active season exists.

## Configuration

File: `backend/app/config.py`

```python
@dataclass
class Config:
    SUBMISSION_TIMEOUT_S: int = 5
    MEMORY_LIMIT_MB: int = 128

    ROUNDS_PER_MATCH: int = 3
    ROUND_TIMES: list[int] = field(default_factory=lambda: [180, 300, 480])
    ROUND_DIFFICULTIES: list[str] = field(default_factory=lambda: ["easy", "medium", "hard"])
    WINS_NEEDED: int = 2

    ANTI_CHEAT_SPEED_THRESHOLDS: dict[str, int] = field(
        default_factory=lambda: {"easy": 8, "medium": 15, "hard": 25}
    )
    ANTI_CHEAT_PASTE_LENGTH_MIN: int = 50
    ANTI_CHEAT_TAB_TIME_SUSPICIOUS_MS: int = 30_000
    ANTI_CHEAT_FLAG_THRESHOLD: float = 0.5
    ANTI_CHEAT_WARN_THRESHOLD: float = 0.3

    MATCHMAKING_INITIAL_RANGE: int = 100
    MATCHMAKING_RANGE_WIDEN: int = 25
    MATCHMAKING_WIDEN_INTERVAL_S: int = 5
    MATCHMAKING_MAX_RANGE: int = 400
    MATCHMAKING_MAX_WAIT_S: int = 60
    MATCHMAKING_SCAN_INTERVAL_S: float = 1.0

    SEASON_DURATION_DAYS: int = 90
    SEASON_SOFT_RESET_BASE: int = 1000
```

What this does:
- Centralizes all tunable game constants.
- Makes the system easy to reason about and adjust.
- `Config` is instantiated once as `CONFIG` at module import.

## Two kinds of models

**In-memory dataclasses (`models.py`)** — for live state:

```python
@dataclass
class Match:
    match_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    players: dict[str, PlayerState] = field(default_factory=dict)
    rounds: list[Round] = field(default_factory=list)
```

Used for: active matches, queued players, online lobby. Fast to access, disappears on server restart.

**Database models (`models_db.py`)** — for persistence:

```python
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: _gen_id(12))
    username = Column(String(30), unique=True, nullable=False, index=True)
    elo = Column(Float, default=1000.0)
    tier = Column(String(20), default="bronze")
```

Used for: users, match records, friendships, refresh tokens, seasons. Survives restarts.

## Why this matters in an interview

You can say:

> "The backend is FastAPI with a single config dataclass for all game constants. Live state is modeled as dataclasses in memory; persistent data uses SQLAlchemy with SQLite. This split keeps the real-time path fast while still tracking user ELO, history, and auth across restarts."

## Common trap

**"Why SQLite and not PostgreSQL?"**

Honest answer: SQLite is zero-config for a portfolio project. The code uses `DATABASE_URL` so switching to PostgreSQL is one environment variable change. `DATABASE_URL` is read in `database.py`.

## Self-check

1. What does FastAPI do in this project?
2. Where do you change the number of rounds per match?
3. What is the difference between `models.py` and `models_db.py`?
4. What happens on server startup in `main.py`?
5. How would you switch to PostgreSQL?

## Code map

| Concept | File |
|---|---|
| FastAPI app | `backend/app/main.py` |
| Game constants | `backend/app/config.py` |
| In-memory models | `backend/app/models.py` |
| Database models | `backend/app/models_db.py` |
| Database setup | `backend/app/database.py` |
| Seasons startup | `backend/app/seasons.py` |
