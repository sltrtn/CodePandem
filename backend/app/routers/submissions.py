from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.judge import run_submission
from app.models import Telemetry
from app.problems import PROBLEMS

router = APIRouter()


class SubmitRequest(BaseModel):
    code: str
    problem_id: str


@router.post("/submit")
async def submit_code(req: SubmitRequest):
    problem = next((p for p in PROBLEMS if p.id == req.problem_id), None)
    if not problem:
        return {"error": "Problem not found"}

    result = await run_submission(req.code, problem)
    return {
        "test_cases_passed": result.test_cases_passed,
        "test_cases_total": result.test_cases_total,
        "time_ms": round(result.time_ms, 1),
        "memory_kb": round(result.memory_kb, 1),
        "output": result.output,
        "error": result.error,
    }


@router.get("/problems")
async def list_problems():
    return [
        {"id": p.id, "title": p.title, "difficulty": p.difficulty}
        for p in PROBLEMS
    ]
