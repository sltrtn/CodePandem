from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import auth, health, submissions
from app.ws import duel, queue

app = FastAPI(title="CodePandem", version="0.2.0")

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
app.include_router(queue.router)
app.include_router(duel.router)


@app.on_event("startup")
def on_startup():
    init_db()
