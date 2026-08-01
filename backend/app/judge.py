from __future__ import annotations

import os

import httpx

from app.config import CONFIG
from app.executor import judge_code
from app.models import Problem, SubmissionResult


JUDGE_MODE = os.getenv("JUDGE_MODE", "process")
JUDGE_URL = os.getenv("JUDGE_URL", "http://judge:9000")


async def _judge_http(code: str, problem: Problem) -> SubmissionResult:
    payload = {
        "code": code,
        "test_cases": problem.test_cases,
        "memory_mb": CONFIG.MEMORY_LIMIT_MB,
        "time_limit_s": CONFIG.SUBMISSION_TIMEOUT_S,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{JUDGE_URL}/judge", json=payload)
    except Exception as exc:
        return SubmissionResult(error=f"Judge unavailable: {exc}")

    if resp.status_code != 200:
        return SubmissionResult(error=f"Judge error: HTTP {resp.status_code}")

    data = resp.json()
    return SubmissionResult(
        test_cases_passed=data.get("test_cases_passed", 0),
        test_cases_total=data.get("test_cases_total", 0),
        time_ms=data.get("time_ms", 0.0),
        memory_kb=data.get("memory_kb", 0.0),
        error=data.get("error"),
    )


async def run_submission(code: str, problem: Problem) -> SubmissionResult:
    if JUDGE_MODE == "http":
        return await _judge_http(code, problem)
    return await judge_code(code, problem)
