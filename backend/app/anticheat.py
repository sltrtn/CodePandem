from __future__ import annotations

import math

from app.config import CONFIG
from app.models import CheatScore, Problem, Telemetry


def check_speed(telemetry: Telemetry, problem: Problem) -> float:
    time_s = telemetry.time_since_match_start_ms / 1000
    threshold = CONFIG.ANTI_CHEAT_SPEED_THRESHOLDS.get(problem.difficulty, 15)
    if time_s < threshold:
        return min(1.0, (threshold - time_s) / threshold)
    return 0.0


def check_paste(telemetry: Telemetry, code: str) -> float:
    score = 0.0
    code_len = len(code.strip())

    if telemetry.keystroke_count == 0 and code_len > CONFIG.ANTI_CHEAT_PASTE_LENGTH_MIN:
        score += 0.7

    if telemetry.paste_event_count == 1 and code_len > 0:
        ratio = telemetry.total_paste_length / code_len
        if ratio > 0.9:
            score += 0.5

    if telemetry.time_since_match_start_ms < 5000 and telemetry.paste_event_count > 0:
        score += 0.3

    if telemetry.burst_paste_count >= 3:
        score += 0.3
    elif telemetry.burst_paste_count >= 2:
        score += 0.15

    return min(1.0, score)


def check_tab_switches(telemetry: Telemetry) -> float:
    if telemetry.tab_switch_count == 0:
        return 0.0

    score = min(0.3, telemetry.tab_switch_count * 0.1)

    if telemetry.total_tab_time_ms > CONFIG.ANTI_CHEAT_TAB_TIME_SUSPICIOUS_MS:
        score += 0.4

    return min(1.0, score)


def check_keystrokes(telemetry: Telemetry, code: str) -> float:
    score = 0.0
    code_len = len(code.strip())
    kps = telemetry.keystrokes_per_second

    if kps > 15:
        score += 0.4
    elif kps < 0.5 and code_len > 100:
        score += 0.3

    return min(1.0, score)


def check_typing_pattern(telemetry: Telemetry) -> float:
    score = 0.0

    events = telemetry.keystroke_events
    if len(events) < 10:
        return 0.0

    intervals = []
    for i in range(1, len(events)):
        dt = events[i].get("timestamp_ms", 0) - events[i - 1].get("timestamp_ms", 0)
        if 0 < dt < 2000:
            intervals.append(dt)

    if not intervals:
        return 0.0

    avg = sum(intervals) / len(intervals)
    variance = sum((x - avg) ** 2 for x in intervals) / len(intervals)
    stddev = math.sqrt(variance)

    if stddev < 5 and len(intervals) > 20:
        score += 0.35

    if avg < 30 and len(intervals) > 15:
        score += 0.2

    bursts = 0
    current_burst = 0
    for dt in intervals:
        if dt < 50:
            current_burst += 1
            if current_burst >= 8:
                bursts += 1
        else:
            current_burst = 0
    if bursts >= 3:
        score += 0.25

    return min(1.0, score)


def check_code_plagiarism(code: str, problem: Problem) -> float:
    code_stripped = code.strip()
    if len(code_stripped) < 20:
        return 0.0

    score = 0.0

    lines = [l.strip() for l in code_stripped.split("\n") if l.strip()]
    if len(lines) > 0:
        unique_lines = set(lines)
        if len(unique_lines) < len(lines) * 0.3 and len(lines) > 5:
            score += 0.2

    for tc in problem.test_cases[:1]:
        output = tc.get("output", "").strip()
        if output and output in code_stripped:
            score += 0.3
            break

    return min(1.0, score)


def calculate_cheat_score(
    telemetry: Telemetry,
    problem: Problem,
    code: str,
) -> CheatScore:
    speed = check_speed(telemetry, problem)
    paste = check_paste(telemetry, code)
    tabs = check_tab_switches(telemetry)
    keys = check_keystrokes(telemetry, code)
    pattern = check_typing_pattern(telemetry)
    plagiarism = check_code_plagiarism(code, problem)

    composite = round(
        speed * 0.20
        + paste * 0.25
        + tabs * 0.15
        + keys * 0.10
        + pattern * 0.15
        + plagiarism * 0.15,
        4,
    )

    flags: list[str] = []
    if speed > 0.2:
        flags.append("speed")
    if paste > 0.2:
        flags.append("paste")
    if tabs > 0.2:
        flags.append("tabs")
    if keys > 0.2:
        flags.append("keystrokes")
    if pattern > 0.2:
        flags.append("typing_pattern")
    if plagiarism > 0.2:
        flags.append("plagiarism")

    return CheatScore(
        composite=composite,
        breakdown={
            "speed": speed,
            "paste": paste,
            "tabs": tabs,
            "keystrokes": keys,
            "typing_pattern": pattern,
            "plagiarism": plagiarism,
        },
        flagged=composite > CONFIG.ANTI_CHEAT_FLAG_THRESHOLD,
        suspicious=composite > CONFIG.ANTI_CHEAT_WARN_THRESHOLD,
    )
