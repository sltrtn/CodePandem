from __future__ import annotations

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


def calculate_cheat_score(
    telemetry: Telemetry,
    problem: Problem,
    code: str,
) -> CheatScore:
    speed = check_speed(telemetry, problem)
    paste = check_paste(telemetry, code)
    tabs = check_tab_switches(telemetry)
    keys = check_keystrokes(telemetry, code)

    composite = round(
        speed * 0.25 + paste * 0.30 + tabs * 0.20 + keys * 0.15,
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

    return CheatScore(
        composite=composite,
        breakdown={"speed": speed, "paste": paste, "tabs": tabs, "keystrokes": keys},
        flagged=composite > CONFIG.ANTI_CHEAT_FLAG_THRESHOLD,
        suspicious=composite > CONFIG.ANTI_CHEAT_WARN_THRESHOLD,
    )
