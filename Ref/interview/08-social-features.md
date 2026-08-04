# Lesson 8 — Social Features: Friends, Challenges, and Custom Lobbies

## What this lesson covers

- Friends system
- Direct challenges
- Custom lobbies
- Spectator mode

## Friends

File: `backend/app/routers/social.py`

A `Friendship` row has `requester_id`, `addressee_id`, and `status` (pending/accepted/declined).

Endpoints:
- `POST /social/friends/request/{user_id}` — send a request
- `POST /social/friends/accept/{user_id}` — accept
- `POST /social/friends/decline/{user_id}` — decline
- `POST /social/friends/remove/{user_id}` — remove
- `GET /social/friends` — list friends with online status
- `GET /social/friends/requests` — list pending requests

Online status is pulled from the in-memory lobby:

```python
online = lobby.get_player(u.id)
friends.append({
    "user_id": u.id,
    "username": u.username,
    "elo": round(u.elo, 1),
    "tier": u.tier,
    "online": online is not None,
    "status": online.status if online else "offline",
})
```

## Direct challenges

File: `backend/app/ws/challenge.py`

WebSocket `/ws/challenge`:
- `challenge_player` → sends a challenge to the target player
- `accept_challenge` → creates a ranked match using the existing lobby WebSockets
- `decline_challenge` → rejects the challenge

Challenges are stored in `matchmaker._pending_challenges`.

## Custom lobbies

File: `backend/app/routers/social.py`

- `POST /social/lobby/create` → host creates a 6-character code
- `POST /social/lobby/join/{code}` → second player joins
- Both players must be online in the lobby
- Creates an unranked match

```python
match = Match()
match.players[host_id] = PlayerState(player_id=host_id, ws=p1.ws)
match.players[player_id] = PlayerState(player_id=player_id, ws=p2.ws)
match.mode = "unranked"
```

## Spectator mode

File: `backend/app/ws/duel.py`

WebSocket `/ws/spectate/{match_id}`:
- Authenticated spectator joins
- Added to match watchers
- All duel state broadcasts also go to watchers

```python
async def _broadcast(match, message):
    for ps in match.players.values():
        await ps.ws.send_json(message)
    await lobby.broadcast_to_watchers(match.match_id, message)
```

## Why this matters in an interview

You can say:

> "Beyond ranked queue, the platform has a social layer: friends with online status, direct challenges via WebSocket, custom lobbies with join codes, and spectator mode. Friends and custom lobbies are unranked; direct challenges are ranked."

## Common trap

**"How do custom lobbies start a match without going through the queue?"**

They create a `Match` directly and attach the players' existing lobby WebSockets to it. This bypasses the matchmaker entirely.

## Self-check

1. How is friendship status stored?
2. How do you know if a friend is online?
3. What is the difference between a direct challenge and a custom lobby?
4. How does spectator mode receive updates?
5. Why are custom lobbies unranked?

## Code map

| Concept | File |
|---|---|
| Friends DB model | `backend/app/models_db.py` |
| Friends routes | `backend/app/routers/social.py` |
| Challenges | `backend/app/ws/challenge.py` |
| Custom lobbies | `backend/app/routers/social.py` |
| Spectators | `backend/app/ws/duel.py` + `backend/app/lobby.py` |
| Lobby state | `backend/app/lobby.py` |
