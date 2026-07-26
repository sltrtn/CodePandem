from app.models import Match, PlayerRoundState, PlayerState, Round, Problem


def test_match_creation():
    m = Match()
    assert m.match_id
    assert m.status == "waiting"


def test_round_defaults():
    r = Round(
        round_number=1,
        problem=Problem(id="test", title="Test"),
        time_limit_s=180,
    )
    assert r.status == "active"
    assert r.problem.id == "test"


def test_player_state_defaults():
    p = PlayerState(player_id="abc")
    assert p.total_score == 0.0
    assert p.round_wins == 0
