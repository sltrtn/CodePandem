from __future__ import annotations

from app.models import Match, PlayerRoundState, Round, SubmissionResult


def score_submission(
    result: SubmissionResult,
    time_limit_ms: float,
) -> float:
    if result.test_cases_total == 0:
        return 0.0

    base = result.test_cases_passed / result.test_cases_total
    speed = max(0.0, 1.0 - (result.time_ms / time_limit_ms))
    return round(base + (speed * 0.01), 6)


def determine_round_winner(rnd: Round) -> str | None:
    items = sorted(rnd.players.items(), key=lambda kv: kv[1].score, reverse=True)
    if len(items) < 2:
        return None
    if items[0][1].score > items[1][1].score:
        return items[0][0]
    return None


def determine_match_winner(match: Match) -> str | None:
    best_pid = None
    best_wins = -1
    for pid, ps in match.players.items():
        if ps.round_wins > best_wins:
            best_wins = ps.round_wins
            best_pid = pid

    winners = [pid for pid, ps in match.players.items() if ps.round_wins == best_wins]
    if len(winners) == 1:
        return winners[0]

    best_score = -1.0
    score_winner = None
    for pid in winners:
        s = match.players[pid].total_score
        if s > best_score:
            best_score = s
            score_winner = pid
    if score_winner and best_score > 0:
        return score_winner

    return None
