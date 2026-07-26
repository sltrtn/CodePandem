from app.scoring import score_submission, determine_round_winner, determine_match_winner
from app.models import Match, PlayerRoundState, PlayerState, Round, Problem, SubmissionResult


def test_score_perfect_fast():
    r = SubmissionResult(test_cases_passed=5, test_cases_total=5, time_ms=100)
    s = score_submission(r, 3000)
    assert s > 1.0


def test_score_partial():
    r = SubmissionResult(test_cases_passed=3, test_cases_total=5, time_ms=100)
    s = score_submission(r, 3000)
    assert 0.6 < s < 0.7


def test_score_zero():
    r = SubmissionResult(test_cases_passed=0, test_cases_total=5, time_ms=100)
    s = score_submission(r, 3000)
    assert s < 0.02


def test_round_winner():
    rnd = Round(
        players={
            "a": PlayerRoundState(player_id="a", score=0.8),
            "b": PlayerRoundState(player_id="b", score=0.6),
        }
    )
    assert determine_round_winner(rnd) == "a"


def test_round_tie():
    rnd = Round(
        players={
            "a": PlayerRoundState(player_id="a", score=0.5),
            "b": PlayerRoundState(player_id="b", score=0.5),
        }
    )
    assert determine_round_winner(rnd) is None


def test_match_winner():
    m = Match()
    m.players["a"] = PlayerState(player_id="a", round_wins=2)
    m.players["b"] = PlayerState(player_id="b", round_wins=1)
    assert determine_match_winner(m) == "a"
