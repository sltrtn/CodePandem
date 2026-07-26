from __future__ import annotations

import asyncio
import os
import resource
import tempfile
import textwrap
import time

from app.config import CONFIG
from app.models import Problem, SubmissionResult


def _build_wrapper(code_file: str, mem_bytes: int) -> str:
    return textwrap.dedent(f"""\
        import sys, resource, io

        try:
            resource.setrlimit(resource.RLIMIT_AS, ({mem_bytes}, {mem_bytes}))
        except ValueError:
            pass

        with open({repr(code_file)}, 'r') as _f:
            _user_code = _f.read()

        _old_stdout = sys.stdout
        sys.stdout = _buf = io.StringIO()

        try:
            exec(compile(_user_code, '<user>', 'exec'))
        except SystemExit:
            pass
        except Exception as e:
            sys.stdout = _old_stdout
            print(f'ERROR: {{e}}', file=sys.stderr)
            sys.exit(1)

        _output = _buf.getvalue().rstrip('\\n')
        sys.stdout = _old_stdout
        print(_output)
    """)


async def _run_single(
    code_file: str, test_input: str, mem_bytes: int
) -> tuple[str, str, float]:
    wrapper_code = _build_wrapper(code_file, mem_bytes)

    start = time.perf_counter()
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-c", wrapper_code,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(input=test_input.encode()),
            timeout=CONFIG.SUBMISSION_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        return "", "Time Limit Exceeded", 0.0

    elapsed_ms = (time.perf_counter() - start) * 1000
    output = stdout_bytes.decode(errors="replace").strip()
    error = None
    if proc.returncode != 0:
        error = stderr_bytes.decode(errors="replace").strip() or "Runtime Error"
    return output, error or "", elapsed_ms


async def run_submission(code: str, problem: Problem) -> SubmissionResult:
    mem_bytes = CONFIG.MEMORY_LIMIT_MB * 1024 * 1024

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir="/tmp"
    ) as f:
        f.write(code)
        code_file = f.name

    total_time = 0.0
    max_memory = 0.0
    passed = 0
    last_error: str | None = None

    try:
        for tc in problem.test_cases:
            test_input = tc.get("input", "")
            output, error, elapsed = await _run_single(code_file, test_input, mem_bytes)
            total_time += elapsed

            try:
                usage = resource.getrusage(resource.RUSAGE_CHILDREN)
                max_memory = max(max_memory, usage.ru_maxrss)
            except Exception:
                pass

            if error:
                last_error = error
                continue

            expected = tc["expected"].strip()
            if output == expected:
                passed += 1
    finally:
        _cleanup(code_file)

    return SubmissionResult(
        test_cases_passed=passed,
        test_cases_total=len(problem.test_cases),
        time_ms=total_time,
        memory_kb=max_memory,
        error=last_error if passed == 0 and last_error else None,
    )


def _cleanup(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass
