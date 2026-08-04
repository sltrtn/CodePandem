# Lesson 6 — Judge System: Isolated Code Execution

## What this lesson covers

- Why the judge is separate from the backend
- How code runs in process mode
- How the HTTP judge worker runs in production
- Security isolation: non-root, memory cap, timeout, read-only filesystem

## Why a separate judge service

The main backend must never run untrusted user code directly. A malicious submission could:
- Infinite loop or fork bomb
- Consume all RAM
- Read files or environment variables
- Crash the server

By moving execution into a separate service, the blast radius is limited. If the judge is compromised, the main backend is not.

## Process mode

File: `backend/app/executor.py`

```python
async def run_case(code, test_input, memory_bytes, timeout_s):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir="/tmp") as f:
        f.write(code)
        code_file = f.name

    wrapper_code = _build_wrapper(code_file, memory_bytes)

    proc = await asyncio.create_subprocess_exec(
        "python3", "-c", wrapper_code,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(...), timeout=timeout_s)
```

The wrapper:
1. Sets `RLIMIT_AS` to cap memory.
2. Reads the user code file.
3. Redirects stdout.
4. Runs the code via `exec(compile(...))`.
5. Prints captured output.

## HTTP judge worker

File: `backend/app/judge_worker.py`

```python
CONCURRENCY = int(os.getenv("JUDGE_CONCURRENCY", "4"))
_semaphore = asyncio.Semaphore(CONCURRENCY)

@app.post("/judge")
async def judge(req: JudgeRequest):
    problem = Problem(test_cases=req.test_cases)
    async with _semaphore:
        result = await judge_code(req.code, problem)
    return {...}
```

The judge is a FastAPI microservice. It exposes a single `/judge` endpoint and limits concurrent executions to prevent resource exhaustion.

## Dispatcher

File: `backend/app/judge.py`

```python
JUDGE_MODE = os.getenv("JUDGE_MODE", "process")
JUDGE_URL = os.getenv("JUDGE_URL", "http://judge:9000")

async def run_submission(code, problem):
    if JUDGE_MODE == "http":
        return await _judge_http(code, problem)
    return await judge_code(code, problem)
```

- `process` mode: backend runs submissions locally (used in tests).
- `http` mode: backend sends submissions to the judge service (used in Docker/Kubernetes).

## Security properties

Dockerfile.judge:
```dockerfile
RUN useradd -m -u 1000 judge
USER judge
```

Kubernetes manifest:
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
```

Plus an `emptyDir` volume mounted at `/tmp` so the judge can still write temp files.

Verified behavior:
```
kubectl exec deploy/judge -- id
uid=1000(judge) gid=1000(judge)
```

## Why this matters in an interview

You can say:

> "User code runs in a dedicated judge microservice, not the main backend. In process mode it uses a subprocess with RLIMIT_AS for a 128 MB memory cap and a 5-second timeout. In production it calls an HTTP judge worker that runs as a non-root user with a read-only root filesystem. Concurrency is limited by a semaphore to prevent resource exhaustion."

## Common trap

**"Is it fully secure?"**

Honest answer: it is a strong isolation layer for a portfolio project, but it is not a full sandbox. For untrusted Python, a true sandbox would use seccomp-bpf, gVisor, or a separate VM per submission. The current design demonstrates the concept and is the right scope for a fresher project.

## Self-check

1. Why is the judge separate from the backend?
2. How is memory capped in process mode?
3. What is the HTTP judge worker's concurrency control?
4. What user does the judge container run as?
5. How is the read-only root filesystem handled?

## Code map

| Concept | File |
|---|---|
| Subprocess execution | `backend/app/executor.py` |
| Judge dispatcher | `backend/app/judge.py` |
| HTTP judge worker | `backend/app/judge_worker.py` |
| Judge Dockerfile | `backend/Dockerfile.judge` |
| K8s judge manifest | `k8s/judge.yaml` |
