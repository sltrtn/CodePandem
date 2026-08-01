from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from app.executor import judge_code
from app.models import Problem, SubmissionResult


CONCURRENCY = int(os.getenv("JUDGE_CONCURRENCY", "4"))
_semaphore = asyncio.Semaphore(CONCURRENCY)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="CodePandem Judge", version="1.0.0", lifespan=lifespan)


class JudgeRequest(BaseModel):
    code: str
    test_cases: list[dict]
    memory_mb: int | None = None
    time_limit_s: int | None = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/judge")
async def judge(req: JudgeRequest) -> dict:
    problem = Problem(test_cases=req.test_cases)
    async with _semaphore:
        result: SubmissionResult = await judge_code(req.code, problem)

    return {
        "test_cases_passed": result.test_cases_passed,
        "test_cases_total": result.test_cases_total,
        "time_ms": round(result.time_ms, 1),
        "memory_kb": round(result.memory_kb, 1),
        "output": result.output,
        "error": result.error,
    }
