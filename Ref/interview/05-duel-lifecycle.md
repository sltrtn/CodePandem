# Lesson 5 — Duel Lifecycle

## What this lesson covers

- From queue to match
- Round timers and state transitions
- Submission flow
- Determining winners
- Persisting results

## Match creation

When the matchmaker pairs two players, it creates:

```python
match = Match()
match.players[pid1] = PlayerState(player_id=pid1, ws=ws1)
match.players[pid2] = PlayerState(player_id=pid2, ws=ws2)
match.mode = mode
match.season_id = get_current_season_id()

problems = get_problems_for_match()
for i, problem in enumerate(problems):
    rnd = Round(
        round_number=i + 1,
        problem=problem,
        time_limit_s=CONFIG.ROUND_TIMES[i],
        status="active" if i == 0 else "pending",
        players={pid1: PlayerRoundState(...), pid2: PlayerRoundState(...)},
    )
    match.rounds.append(rnd)
```

The match always has 3 rounds: easy (180s), medium (300s), hard (480s). The first round is active immediately.

## Players connect to the duel

File: `backend/app/ws/duel.py`

```python
@router.websocket("/ws/duel/{match_id}")
async def ws_duel(ws: WebSocket, match_id: str):
    await ws.accept()
    user = authenticate_ws_token(...)
    match = matchmaker.get_match(match_id)
    if player_id not in match.players:
        await ws.close()
        return
    match.players[player_id].ws = ws
    await ws.send_json(_serialize_match(match, usernames))
    asyncio.create_task(_start_round_timer(match, match.rounds[0]))
```

Each player stores their WebSocket on the `PlayerState`. The server sends the full match state and starts a timer for the active round.

## Submission flow

When a player submits:

```python
if msg_type == "submit":
    code = data.get("code", "")
    telemetry_raw = data.get("telemetry", {})
    telemetry = Telemetry(...)

    result = await run_submission(code, rnd.problem)
    cheat = calculate_cheat_score(telemetry, rnd.problem, code)
    result.cheat_score = cheat.composite
    result.suspicious = cheat.suspicious

    round_score = score_submission(result, time_limit_ms)
    prs.score += round_score
    ps.total_score += round_score

    await _broadcast(match, {"type": "duel_state", ...})
```

Steps:
1. Run code through the judge.
2. Evaluate anti-cheat telemetry.
3. Compute score.
4. Update player state.
5. Broadcast to both players and spectators.

## Round timer

```python
async def _start_round_timer(match: Match, rnd: Round):
    await asyncio.sleep(rnd.time_limit_s)
    if rnd.status != "active":
        return
    await _finish_round(match, rnd)
```

If the timer expires, the round finishes automatically. The first player to 2 round wins wins the match.

## Winner determination

Round winner:
```python
def determine_round_winner(rnd: Round):
    items = sorted(rnd.players.items(), key=lambda kv: kv[1].score, reverse=True)
    if items[0][1].score > items[1][1].score:
        return items[0][0]
    return None
```

Match winner:
```python
def determine_match_winner(match: Match):
    # first to 2 round wins, or best round wins after 3 rounds, then total score
```

## Persisting results

File: `backend/app/ws/duel.py` `_persist_match`

```python
rec = MatchRecord(
    id=match.match_id,
    player1_id=pids[0],
    player2_id=pids[1],
    winner_id=match.winner,
    rounds_played=len(match.rounds),
    mode=match.mode,
    season_id=season_id,
)

# update user ELO, wins/losses/draws, tier
# update season stats
```

Only ranked matches update ELO and season stats.

## Why this matters in an interview

You can say:

> "A duel is a state machine. Three rounds with escalating difficulty and time limits. Players submit code through the duel WebSocket; the judge runs it, anti-cheat scores it, and the result is broadcast to both players and spectators. When a player reaches two round wins or all rounds finish, the match is persisted and ELO is updated."

## Common trap

**"How do you handle a player disconnecting mid-duel?"**

Current behavior: the match continues. The player can reconnect to the same `/ws/duel/{match_id}` because match state is keyed by match_id. There is no explicit disconnect winner logic; this is a known limitation.

## Self-check

1. How many rounds are in a match? What are the time limits?
2. What happens when a player submits code?
3. How is the round winner determined?
4. How is the match winner determined?
5. What is persisted after a match?

## Code map

| Concept | File |
|---|---|
| Match + Round dataclasses | `backend/app/models.py` |
| Duel WebSocket | `backend/app/ws/duel.py` |
| Scoring | `backend/app/scoring.py` |
| Match persistence | `backend/app/ws/duel.py` `_persist_match` |
| ELO calculation | `backend/app/ws/duel.py` `_calc_elo_change` |
| Season stats | `backend/app/seasons.py` |
