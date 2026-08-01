from __future__ import annotations

import asyncio
import os
import resource
import tempfile
import textwrap
import time
from dataclasses import dataclass

from app.config import CONFIG
from app.models import Problem, SubmissionResult


@dataclass
class ExecutionResult:
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    elapsed_ms: float = 0.0


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


def _cleanup(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


async def run_case(
    code: str, test_input: str, memory_bytes: int, timeout_s: int
) -> ExecutionResult:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir="/tmp"
    ) as f:
        f.write(code)
        code_file = f.name

    try:
        wrapper_code = _build_wrapper(code_file, memory_bytes)

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
                timeout=timeout_s,
            )
        except asyncio.TimeoutError:
            return ExecutionResult(
                stderr="Time Limit Exceeded", returncode=-1, elapsed_ms=0.0
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        output = stdout_bytes.decode(errors="replace").strip()
        stderr = stderr_bytes.decode(errors="replace").strip()
        error = None
        if proc.returncode != 0:
            error = stderr or "Runtime Error"

        return ExecutionResult(
            stdout=output,
            stderr=error or stderr,
            returncode=proc.returncode,
            elapsed_ms=elapsed_ms,
        )
    finally:
        _cleanup(code_file)


async def judge_code(code: str, problem: Problem) -> SubmissionResult:
    mem_bytes = CONFIG.MEMORY_LIMIT_MB * 1024 * 1024
    timeout_s = CONFIG.SUBMISSION_TIMEOUT_S

    total_time = 0.0
    max_memory = 0.0
    passed = 0
    last_error: str | None = None
    last_output: str = ""

    for tc in problem.test_cases:
        test_input = tc.get("input", "")
        result = await run_case(code, test_input, mem_bytes, timeout_s)
        total_time += result.elapsed_ms
        last_output = result.stdout

        try:
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            max_memory = max(max_memory, usage.ru_maxrss)
        except Exception:
            pass

        if result.stderr:
            last_error = result.stderr
            continue

        expected = tc["expected"].strip()
        if result.stdout == expected:
            passed += 1

    return SubmissionResult(
        test_cases_passed=passed,
        test_cases_total=len(problem.test_cases),
        time_ms=total_time,
        memory_kb=max_memory,
        output=last_output,
        error=last_error if passed == 0 and last_error else None,
    )
