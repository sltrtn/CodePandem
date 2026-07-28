from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import auth, health, seasons, social, submissions
from app.seasons import get_current_season
from app.ws import challenge, duel, lobby_ws, queue

app = FastAPI(title="CodePandem", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
