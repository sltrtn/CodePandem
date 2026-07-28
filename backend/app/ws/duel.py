from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.anticheat import calculate_cheat_score
from app.auth import authenticate_ws_token
from app.config import CONFIG
from app.database import SessionLocal
from app.judge import run_submission
from app.lobby import lobby
from app.matchmaking import matchmaker
from app.models import (
    Match,
    PlayerRoundState,
    Round,
    SubmissionResult,
    Telemetry,
)
from app.scoring import determine_match_winner, determine_round_winner, score_submission

router = APIRouter()


def _serialize_problem(problem):
    return {
        "id": problem.id,
        "title": problem.title,
        "description": problem.description,
        "difficulty": problem.difficulty,
    }


def _serialize_round(rnd: Round) -> dict:
    players = {}
    for pid, prs in rnd.players.items():
        lr = prs.last_result
        players[pid] = {
            "player_id": pid,
            "score": round(prs.score, 4),
            "submissions": prs.submissions,
            "test_cases_passed": lr.test_cases_passed if lr else 0,
            "test_cases_total": lr.test_cases_total if lr else rnd.problem.test_cases.__len__(),
            "time_ms": round(lr.time_ms, 1) if lr else 0,
            "memory_kb": round(lr.memory_kb, 1) if lr else 0,
            "suspicious": lr.suspicious if lr else False,
        }
    return {
        "round_number": rnd.round_number,
        "problem": _serialize_problem(rnd.problem),
        "time_limit_s": rnd.time_limit_s,
        "status": rnd.status,
        "winner": rnd.winner,
        "players": players,
    }


def _serialize_match(match: Match, usernames: dict[str, str]) -> dict:
    players = {}
    for pid, ps in match.players.items():
        players[pid] = {
            "player_id": pid,
            "username": usernames.get(pid, pid),
            "round_wins": ps.round_wins,
            "total_score": round(ps.total_score, 4),
        }
    return {
        "type": "match_state",
        "match_id": match.match_id,
        "current_round": match.current_round,
        "status": match.status,
        "winner": match.winner,
        "players": players,
        "round": _serialize_round(match.rounds[match.current_round - 1]),
    }


def _serialize_round_over(rnd: Round, winner: str | None, match: Match, usernames: dict[str, str]) -> dict:
    return {
        "type": "round_over",
        "round_number": rnd.round_number,
        "winner": winner,
        "round": _serialize_round(rnd),
        "players": {
            pid: {"round_wins": ps.round_wins, "total_score": round(ps.total_score, 4), "username": usernames.get(pid, pid)}
            for pid, ps in match.players.items()
        },
    }


async def _broadcast(match: Match, message: dict) -> None:
    for ps in match.players.values():
        if ps.ws and ps.ws.client_state.name == "CONNECTED":
            try:
                await ps.ws.send_json(message)
            except Exception:
                pass
    await lobby.broadcast_to_watchers(match.match_id, message)


async def _start_round_timer(match: Match, rnd: Round) -> None:
    await asyncio.sleep(rnd.time_limit_s)
    if rnd.status != "active":
        return
    await _finish_round(match, rnd)


async def _finish_round(match: Match, rnd: Round) -> None:
    if rnd.status != "active":
        return
    rnd.status = "finished"

    winner_id = determine_round_winner(rnd)
    rnd.winner = winner_id
    if winner_id and winner_id in match.players:
        match.players[winner_id].round_wins += 1

    match.current_round = rnd.round_number

    usernames = getattr(match, "_usernames", {})
    await _broadcast(match, _serialize_round_over(rnd, winner_id, match, usernames))

    for ps in match.players.values():
        if ps.round_wins >= CONFIG.WINS_NEEDED:
            match.winner = ps.player_id
            match.status = "match_over"
            await _broadcast(match, {
                "type": "match_over",
                "winner": match.winner,
                "players": {
                    pid: {"round_wins": p.round_wins, "total_score": round(p.total_score, 4), "username": usernames.get(pid, pid)}
                    for pid, p in match.players.items()
                },
                "rounds": [_serialize_round(r) for r in match.rounds],
            })
            matchmaker.remove_match(match.match_id)
            _persist_match(match)
            return

    if rnd.round_number >= CONFIG.ROUNDS_PER_MATCH:
        final_winner = determine_match_winner(match)
        match.winner = final_winner
        match.status = "match_over"
        await _broadcast(match, {
            "type": "match_over",
            "winner": match.winner,
            "players": {
                pid: {"round_wins": p.round_wins, "total_score": round(p.total_score, 4), "username": usernames.get(pid, pid)}
                for pid, p in match.players.items()
            },
            "rounds": [_serialize_round(r) for r in match.rounds],
        })
        matchmaker.remove_match(match.match_id)
        _persist_match(match)
        return

    next_rnd = match.rounds[rnd.round_number]
    next_rnd.status = "active"
    match.current_round = next_rnd.round_number
    match.status = "round_active"

    await _broadcast(match, {
        "type": "round_start",
        "round": _serialize_round(next_rnd),
        "players": {
            pid: {"round_wins": p.round_wins, "total_score": round(p.total_score, 4), "username": usernames.get(pid, pid)}
            for pid, p in match.players.items()
        },
    })

    asyncio.create_task(_start_round_timer(match, next_rnd))


def _persist_match(match: Match) -> None:
    from app.models_db import MatchRecord, Season, User, UserSeasonStats

    usernames = getattr(match, "_usernames", {})
    db = SessionLocal()
    try:
        pids = list(match.players.keys())
        if len(pids) != 2:
            return

        is_ranked = match.mode == "ranked"
        season_id = match.season_id if is_ranked else None

        rec = MatchRecord(
            id=match.match_id,
            player1_id=pids[0],
            player2_id=pids[1],
            winner_id=match.winner,
            rounds_played=len(match.rounds),
            mode=match.mode,
            season_id=season_id,
            status="completed",
        )

        if is_ranked:
            rec.player1_elo_change = _calc_elo_change(match, pids[0])
            rec.player2_elo_change = _calc_elo_change(match, pids[1])
        else:
            rec.player1_elo_change = 0.0
            rec.player2_elo_change = 0.0

        db.add(rec)

        for pid in pids:
            user = db.query(User).filter(User.id == pid).first()
            if not user:
                continue

            if is_ranked:
                elo_change = rec.player1_elo_change if pid == pids[0] else rec.player2_elo_change
                user.elo += elo_change
                if user.elo > user.highest_elo:
                    user.highest_elo = user.elo
                user.update_tier()

                if match.winner == pid:
                    user.wins += 1
                elif match.winner:
                    user.losses += 1
                else:
                    user.draws += 1

                if season_id:
                    stats = (
                        db.query(UserSeasonStats)
                        .filter(
                            UserSeasonStats.user_id == pid,
                            UserSeasonStats.season_id == season_id,
                        )
                        .first()
                    )
                    if not stats:
                        stats = UserSeasonStats(
                            user_id=pid,
                            season_id=season_id,
                            season_elo=user.elo - elo_change,
                        )
                        db.add(stats)
                    stats.season_elo += elo_change
                    if stats.season_elo > stats.highest_season_elo:
                        stats.highest_season_elo = stats.season_elo
                    stats.games_played += 1
                    if match.winner == pid:
                        stats.wins += 1
                    elif match.winner:
                        stats.losses += 1
                    else:
                        stats.draws += 1
                    stats.updated_at = datetime.now(timezone.utc)

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _calc_elo_change(match: Match, player_id: str) -> float:
    from app.models_db import User
    from app.database import SessionLocal

    pids = list(match.players.keys())
    opponent_id = pids[1] if pids[0] == player_id else pids[0]

    db = SessionLocal()
    try:
        player = db.query(User).filter(User.id == player_id).first()
        opponent = db.query(User).filter(User.id == opponent_id).first()
        if not player or not opponent:
            return 0.0

        K = 32
        expected = 1 / (1 + 10 ** ((opponent.elo - player.elo) / 400))
        if match.winner == player_id:
            score = 1.0
        elif match.winner:
            score = 0.0
        else:
            score = 0.5
        return round(K * (score - expected), 1)
    finally:
        db.close()


@router.websocket("/ws/duel/{match_id}")
async def ws_duel(ws: WebSocket, match_id: str) -> None:
    await ws.accept()

    token = ws.query_params.get("token")
    if not token:
        await ws.send_json({"type": "error", "message": "Authentication required"})
        await ws.close()
        return

    db = SessionLocal()
    try:
        user = authenticate_ws_token(token, db)
        if not user:
            await ws.send_json({"type": "error", "message": "Invalid token"})
            await ws.close()
            return
        player_id = user.id
        username = user.username
    finally:
        db.close()

    match = matchmaker.get_match(match_id)
    if not match:
        await ws.send_json({"type": "error", "message": "Match not found"})
        await ws.close()
        return

    if player_id not in match.players:
        await ws.send_json({"type": "error", "message": "You are not in this match"})
        await ws.close()
        return

    match.players[player_id].ws = ws

    usernames = getattr(match, "_usernames", {})
    usernames[player_id] = username
    match._usernames = usernames

    await ws.send_json(_serialize_match(match, usernames))

    match_start_ms = int(time.time() * 1000)

    asyncio.create_task(_start_round_timer(match, match.rounds[match.current_round - 1]))

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "submit":
                code = data.get("code", "")
                telemetry_raw = data.get("telemetry", {})

                telemetry = Telemetry(
                    paste_events=telemetry_raw.get("paste_events", []),
                    tab_switches=telemetry_raw.get("tab_switches", []),
                    keystroke_count=telemetry_raw.get("keystroke_count", 0),
                    keystrokes_per_second=telemetry_raw.get("keystrokes_per_second", 0.0),
                    time_since_match_start_ms=int(time.time() * 1000) - match_start_ms,
                    paste_event_count=telemetry_raw.get("paste_event_count", 0),
                    total_paste_length=telemetry_raw.get("total_paste_length", 0),
                    tab_switch_count=telemetry_raw.get("tab_switch_count", 0),
                    total_tab_time_ms=telemetry_raw.get("total_tab_time_ms", 0),
                    keystroke_events=telemetry_raw.get("keystroke_events", []),
                    avg_key_interval_ms=telemetry_raw.get("avg_key_interval_ms", 0.0),
                    key_interval_stddev=telemetry_raw.get("key_interval_stddev", 0.0),
                    burst_paste_count=telemetry_raw.get("burst_paste_count", 0),
                    max_burst_length=telemetry_raw.get("max_burst_length", 0),
                )

                rnd = match.rounds[match.current_round - 1]
                if rnd.status != "active":
                    await ws.send_json({"type": "error", "message": "Round not active"})
                    continue

                result = await run_submission(code, rnd.problem)

                cheat = calculate_cheat_score(telemetry, rnd.problem, code)
                result.cheat_score = cheat.composite
                result.cheat_flags = list(cheat.breakdown.keys()) if cheat.suspicious else []
                result.suspicious = cheat.suspicious

                time_limit_ms = rnd.time_limit_s * 1000
                round_score = score_submission(result, time_limit_ms)

                prs = rnd.players.get(player_id)
                if prs:
                    prs.score += round_score
                    prs.submissions += 1
                    prs.last_result = result
                    prs.total_time_ms += result.time_ms

                ps = match.players.get(player_id)
                if ps:
                    ps.total_score += round_score

                await _broadcast(match, {
                    "type": "duel_state",
                    "current_round": match.current_round,
                    "player_id": player_id,
                    "submission_result": {
                        "test_cases_passed": result.test_cases_passed,
                        "test_cases_total": result.test_cases_total,
                        "time_ms": round(result.time_ms, 1),
                        "memory_kb": round(result.memory_kb, 1),
                        "score": round(round_score, 4),
                        "error": result.error,
                        "suspicious": result.suspicious,
                        "cheat_score": round(cheat.composite, 4),
                        "cheat_breakdown": cheat.breakdown,
                        "cheat_flags": list(cheat.breakdown.keys()) if cheat.suspicious else [],
                    },
                    "players": {
                        pid: {
                            "player_id": pid,
                            "username": usernames.get(pid, pid),
                            "round_score": round(rnd.players[pid].score, 4),
                            "submissions": rnd.players[pid].submissions,
                            "suspicious": rnd.players[pid].last_result.suspicious if rnd.players[pid].last_result else False,
                            "cheat_score": round(rnd.players[pid].last_result.cheat_score, 4) if rnd.players[pid].last_result else 0,
                        }
                        for pid in rnd.players
                    },
                })

            if msg_type == "chat":
                text = data.get("text", "").strip()
                if text and len(text) <= 500:
                    await _broadcast(match, {
                        "type": "chat",
                        "player_id": player_id,
                        "username": username,
                        "text": text,
                    })

    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@router.websocket("/ws/spectate/{match_id}")
async def ws_spectate(ws: WebSocket, match_id: str) -> None:
    await ws.accept()

    token = ws.query_params.get("token")
    if not token:
        await ws.send_json({"type": "error", "message": "Authentication required"})
        await ws.close()
        return

    db = SessionLocal()
    try:
        user = authenticate_ws_token(token, db)
        if not user:
            await ws.send_json({"type": "error", "message": "Invalid token"})
            await ws.close()
            return
        viewer_id = user.id
        viewer_name = user.username
    finally:
        db.close()

    match = matchmaker.get_match(match_id)
    if not match:
        await ws.send_json({"type": "error", "message": "Match not found"})
        await ws.close()
        return

    lobby.add_watcher(f"{viewer_id}:{match_id}", ws)

    usernames = getattr(match, "_usernames", {})
    await ws.send_json({
        "type": "spectate_state",
        "match_id": match_id,
        "current_round": match.current_round,
        "status": match.status,
        "winner": match.winner,
        "players": {
            pid: {
                "player_id": pid,
                "username": usernames.get(pid, pid),
                "round_wins": ps.round_wins,
                "total_score": round(ps.total_score, 4),
            }
            for pid, ps in match.players.items()
        },
        "round": _serialize_round(match.rounds[match.current_round - 1]) if match.rounds else None,
    })

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        lobby.remove_watcher(f"{viewer_id}:{match_id}")
        try:
            await ws.close()
        except Exception:
            pass


@router.websocket("/ws/rematch/{match_id}")
async def ws_rematch(ws: WebSocket, match_id: str) -> None:
    await ws.accept()

    token = ws.query_params.get("token")
    if not token:
        await ws.send_json({"type": "error", "message": "Authentication required"})
        await ws.close()
        return

    db = SessionLocal()
    try:
        user = authenticate_ws_token(token, db)
        if not user:
            await ws.send_json({"type": "error", "message": "Invalid token"})
            await ws.close()
            return
        player_id = user.id
        username = user.username
    finally:
        db.close()

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "request_rematch":
                both_ready = matchmaker.request_rematch(match_id, player_id)
                await ws.send_json({
                    "type": "rematch_requested",
                    "player_id": player_id,
                    "both_ready": both_ready,
                })

                if both_ready:
                    match = matchmaker.get_match(match_id)
                    if match:
                        pids = list(match.players.keys())
                        usernames = getattr(match, "_usernames", {})
                        for pid in pids:
                            await ws.send_json({
                                "type": "rematch_accepted",
                                "match_id": match_id,
                                "opponent": usernames.get(
                                    pids[1] if pid == pids[0] else pids[0], "Unknown"
                                ),
                            })

            elif msg_type == "cancel_rematch":
                matchmaker.clear_rematch(match_id)
                await ws.send_json({"type": "rematch_cancelled"})

    except WebSocketDisconnect:
        pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
