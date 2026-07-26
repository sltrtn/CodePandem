import random

from app.models import Problem

PROBLEMS: list[Problem] = [
    # ── EASY ──────────────────────────────────────────────
    Problem(
        id="easy_1",
        title="Two Sum",
        description=(
            "Given a list of integers `nums` and an integer `target`, return the "
            "indices of the two numbers that add up to `target`.\n\n"
            "The input will be provided as a single line: first the list, then the "
            "target, separated by a pipe `|`.\n\n"
            "Output the two indices separated by a space, in ascending order.\n\n"
            "Example:\n"
            "  Input:  [2,7,11,15] | 9\n"
            "  Output: 0 1"
        ),
        difficulty="easy",
        test_cases=[
            {"input": "[2,7,11,15] | 9", "expected": "0 1"},
            {"input": "[3,2,4] | 6", "expected": "1 2"},
            {"input": "[3,3] | 6", "expected": "0 1"},
        ],
    ),
    Problem(
        id="easy_2",
        title="Reverse String",
        description=(
            "Given a string `s`, reverse it and print the result.\n\n"
            "Input: a single line containing the string.\n"
            "Output: the reversed string.\n\n"
            "Example:\n"
            "  Input:  hello\n"
            "  Output: olleh"
        ),
        difficulty="easy",
        test_cases=[
            {"input": "hello", "expected": "olleh"},
            {"input": "abcdef", "expected": "fedcba"},
            {"input": "a", "expected": "a"},
        ],
    ),
    Problem(
        id="easy_3",
        title="FizzBuzz",
        description=(
            "Print numbers from 1 to `n` (inclusive), one per line.\n"
            "For multiples of 3 print `Fizz`, for multiples of 5 print `Buzz`,\n"
            "for multiples of both print `FizzBuzz`, otherwise print the number.\n\n"
            "Input: a single integer `n`.\n\n"
            "Example (n=5):\n"
            "  1\n  2\n  Fizz\n  4\n  Buzz"
        ),
        difficulty="easy",
        test_cases=[
            {"input": "5", "expected": "1\n2\nFizz\n4\nBuzz"},
            {"input": "3", "expected": "1\n2\nFizz"},
            {"input": "15", "expected": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz"},
        ],
    ),

    # ── MEDIUM ────────────────────────────────────────────
    Problem(
        id="med_1",
        title="Valid Parentheses",
        description=(
            "Given a string containing only `()[]{}`, determine if the input "
            "is valid.\n\n"
            "Input: a single line of characters.\n"
            "Output: `True` if valid, `False` otherwise.\n\n"
            "Examples:\n"
            "  Input:  ()[]{}\n"
            "  Output: True\n"
            "  Input:  (]\n"
            "  Output: False"
        ),
        difficulty="medium",
        test_cases=[
            {"input": "()[]{}", "expected": "True"},
            {"input": "(]", "expected": "False"},
            {"input": "([)]", "expected": "False"},
            {"input": "{[]}", "expected": "True"},
        ],
    ),
    Problem(
        id="med_2",
        title="Longest Substring Without Repeating",
        description=(
            "Given a string `s`, find the length of the longest substring "
            "without repeating characters.\n\n"
            "Input: a single line containing the string.\n"
            "Output: a single integer.\n\n"
            "Examples:\n"
            "  Input:  abcabcbb\n"
            "  Output: 3\n"
            "  Input:  bbbbb\n"
            "  Output: 1\n"
            "  Input:  pwwkew\n"
            "  Output: 3"
        ),
        difficulty="medium",
        test_cases=[
            {"input": "abcabcbb", "expected": "3"},
            {"input": "bbbbb", "expected": "1"},
            {"input": "pwwkew", "expected": "3"},
            {"input": "", "expected": "0"},
        ],
    ),
    Problem(
        id="med_3",
        title="Group Anagrams",
        description=(
            "Given a list of strings, group anagrams together.\n\n"
            "Input: space-separated words on a single line.\n"
            "Output: groups separated by `|`, each group's words sorted "
            "alphabetically and joined by commas.\nGroups themselves sorted "
            "by their first word.\n\n"
            "Example:\n"
            "  Input:  eat tea tan ate nat bat\n"
            "  Output: ate,eat,tea|bat|nat,tan"
        ),
        difficulty="medium",
        test_cases=[
            {"input": "eat tea tan ate nat bat", "expected": "ate,eat,tea|bat|nat,tan"},
            {"input": "a b c ab bc ca abc", "expected": "a|ab|abc|b|bc|c|ca"},
        ],
    ),

    # ── HARD ──────────────────────────────────────────────
    Problem(
        id="hard_1",
        title="Merge Intervals",
        description=(
            "Given a list of intervals `[start, end]`, merge all overlapping "
            "intervals and return the result.\n\n"
            "Input: space-separated intervals in format `start-end`.\n"
            "Output: merged intervals in the same format, sorted by start.\n\n"
            "Examples:\n"
            "  Input:  1-3 2-6 8-10 15-18\n"
            "  Output: 1-6 8-10 15-18\n"
            "  Input:  1-4 4-5\n"
            "  Output: 1-5"
        ),
        difficulty="hard",
        test_cases=[
            {"input": "1-3 2-6 8-10 15-18", "expected": "1-6 8-10 15-18"},
            {"input": "1-4 4-5", "expected": "1-5"},
            {"input": "1-4 0-4", "expected": "0-4"},
        ],
    ),
    Problem(
        id="hard_2",
        title="Minimum Window Substring",
        description=(
            "Given two strings `s` and `t`, find the minimum window in `s` "
            "that contains all characters of `t`.\n\n"
            "Input: two lines — first line is `s`, second line is `t`.\n"
            "Output: the minimum window substring, or empty string if none.\n\n"
            "Examples:\n"
            "  s: ADOBECODEBANC\n"
            "  t: ABC\n"
            "  Output: BANC"
        ),
        difficulty="hard",
        test_cases=[
            {"input": "ADOBECODEBANC\nABC", "expected": "BANC"},
            {"input": "a\na", "expected": "a"},
            {"input": "a\naa", "expected": ""},
        ],
    ),
    Problem(
        id="hard_3",
        title="Trapping Rain Water",
        description=(
            "Given `n` non-negative integers representing an elevation map "
            "where the width of each bar is 1, compute how much water it can "
            "trap after raining.\n\n"
            "Input: space-separated integers on a single line.\n"
            "Output: a single integer — total trapped water.\n\n"
            "Examples:\n"
            "  Input:  0 1 0 2 1 0 1 3 2 1 2 1\n"
            "  Output: 6\n"
            "  Input:  4 2 0 3 2 5\n"
            "  Output: 9"
        ),
        difficulty="hard",
        test_cases=[
            {"input": "0 1 0 2 1 0 1 3 2 1 2 1", "expected": "6"},
            {"input": "4 2 0 3 2 5", "expected": "9"},
            {"input": "1 1 1", "expected": "0"},
        ],
    ),
]

_BY_DIFFICULTY: dict[str, list[Problem]] = {}
for _p in PROBLEMS:
    _BY_DIFFICULTY.setdefault(_p.difficulty, []).append(_p)


def get_random_problem(difficulty: str) -> Problem:
    pool = _BY_DIFFICULTY[difficulty]
    return random.choice(pool)


def get_problems_for_match() -> list[Problem]:
    used: set[str] = set()
    result: list[Problem] = []
    for diff in ["easy", "medium", "hard"]:
        available = [p for p in _BY_DIFFICULTY[diff] if p.id not in used]
        chosen = random.choice(available)
        used.add(chosen.id)
        result.append(chosen)
    return result
