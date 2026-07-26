from app.anticheat import calculate_cheat_score
from app.models import Problem, Telemetry


def test_normal_submission_low_score():
    t = Telemetry(
        keystroke_count=200,
        keystrokes_per_second=3.0,
        time_since_match_start_ms=30_000,
    )
    cs = calculate_cheat_score(t, Problem(difficulty="medium"), "def solve(): pass")
    assert cs.composite < 0.3
    assert not cs.flagged


def test_paste_fast_high_score():
    t = Telemetry(
        keystroke_count=0,
        keystrokes_per_second=0,
        time_since_match_start_ms=2000,
        paste_event_count=1,
        total_paste_length=200,
    )
    code = "x" * 200
    cs = calculate_cheat_score(t, Problem(difficulty="medium"), code)
    assert cs.composite > 0.4
    assert cs.suspicious


def test_tab_switches():
    t = Telemetry(
        keystroke_count=100,
        keystrokes_per_second=2.0,
        time_since_match_start_ms=60_000,
        tab_switch_count=5,
        total_tab_time_ms=45_000,
    )
    cs = calculate_cheat_score(t, Problem(difficulty="hard"), "def solve(): pass")
    assert cs.composite > 0.1


def test_impossible_speed():
    t = Telemetry(
        keystroke_count=100,
        keystrokes_per_second=3.0,
        time_since_match_start_ms=3000,
    )
    cs = calculate_cheat_score(t, Problem(difficulty="hard"), "def solve(): pass")
    assert cs.composite > 0.2
