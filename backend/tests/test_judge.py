import asyncio
from app.judge import run_submission
from app.models import Problem


def _run(code, problem):
    return asyncio.run(run_submission(code, problem))


def test_correct_answer():
    p = Problem(test_cases=[{"input": "5", "expected": "1\n2\nFizz\n4\nBuzz"}])
    code = '''n = int(input())
for i in range(1, n+1):
    if i % 15 == 0: print("FizzBuzz")
    elif i % 3 == 0: print("Fizz")
    elif i % 5 == 0: print("Buzz")
    else: print(i)
'''
    r = _run(code, p)
    assert r.test_cases_passed == 1
    assert r.error is None


def test_wrong_answer():
    p = Problem(test_cases=[{"input": "", "expected": "hello"}])
    r = _run('print("world")', p)
    assert r.test_cases_passed == 0
    assert r.error is None


def test_syntax_error():
    p = Problem(test_cases=[{"input": "", "expected": ""}])
    r = _run("def foo(", p)
    assert r.test_cases_passed == 0
    assert r.error is not None


def test_runtime_error():
    p = Problem(test_cases=[{"input": "", "expected": ""}])
    r = _run("print(1/0)", p)
    assert r.test_cases_passed == 0
    assert r.error is not None


def test_timeout():
    p = Problem(test_cases=[{"input": "", "expected": ""}])
    r = _run("import time; time.sleep(10)", p)
    assert r.test_cases_passed == 0
    assert r.error == "Time Limit Exceeded"


def test_multiple_test_cases():
    p = Problem(test_cases=[
        {"input": "[2,7,11,15] | 9", "expected": "0 1"},
        {"input": "[3,2,4] | 6", "expected": "1 2"},
        {"input": "[3,3] | 6", "expected": "0 1"},
    ])
    code = '''import sys, ast
line = input().strip()
nums_s, target_s = line.split(" | ")
nums = ast.literal_eval(nums_s)
target = int(target_s)
for i in range(len(nums)):
    for j in range(i+1, len(nums)):
        if nums[i] + nums[j] == target:
            print(f"{i} {j}")
            sys.exit()
'''
    r = _run(code, p)
    assert r.test_cases_passed == 3
    assert r.time_ms > 0
