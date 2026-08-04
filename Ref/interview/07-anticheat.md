# Lesson 7 — Anti-Cheat Telemetry and Scoring

## What this lesson covers

- What telemetry is collected
- Each heuristic
- How the composite cheat score is computed
- What happens to suspicious submissions

## Telemetry collected

File: `backend/app/models.py`

```python
@dataclass
class Telemetry:
    paste_events: list[dict]
    tab_switches: list[dict]
    keystroke_count: int
    keystrokes_per_second: float
    time_since_match_start_ms: int
    paste_event_count: int
    total_paste_length: int
    tab_switch_count: int
    total_tab_time_ms: int
    keystroke_events: list[dict]
    avg_key_interval_ms: float
    key_interval_stddev: float
    burst_paste_count: int
    max_burst_length: int
```

The frontend sends this with every submission.

## Heuristics

File: `backend/app/anticheat.py`

### Speed
- Compare time since match start to difficulty threshold (8s easy, 15s medium, 25s hard).
- Faster submission = higher score.

### Paste
- Zero keystrokes + code longer than 50 chars → 0.7.
- Paste ratio > 90% of total code → 0.5.
- Multiple burst pastes → up to 0.3.

### Tab switches
- Each switch adds 0.1, capped at 0.3.
- More than 30s outside tab → +0.4.

### Keystrokes
- >15 KPS or <0.5 KPS with long code → suspicious.

### Typing pattern
- Low interval stddev (<5ms) with many keystrokes → robotic typing.
- Very fast average (<30ms) or repeated bursts → suspicious.

### Plagiarism
- Repeated lines in code.
- Hardcoded expected output in source.

## Composite score

```python
composite = (
    speed * 0.20
    + paste * 0.25
    + tabs * 0.15
    + keys * 0.10
    + pattern * 0.15
    + plagiarism * 0.15
)
```

Thresholds:
- `> 0.3` → suspicious
- `> 0.5` → flagged

Flags are attached to the submission result and broadcast to all clients.

## Why this matters in an interview

You can say:

> "Anti-cheat collects behavioral telemetry on every submission: paste events, tab switches, keystroke timing, and code patterns. Each signal is scored, then combined into a weighted composite. Scores above 0.3 are suspicious, above 0.5 are flagged, and the breakdown is shown to players so flagged submissions are transparent."

## Common trap

**"Can this prove someone cheated?"**

No. It is heuristic. It flags suspicious behavior, not proof. A strong answer is that it raises alerts and can trigger review, but a human or stricter verification step is needed for enforcement.

## Self-check

1. What telemetry is sent with each submission?
2. Name the six anti-cheat checks.
3. What are the weights in the composite score?
4. What is the difference between suspicious and flagged?
5. Why is anti-cheat heuristic, not deterministic?

## Code map

| Concept | File |
|---|---|
| Telemetry model | `backend/app/models.py` |
| Cheat heuristics | `backend/app/anticheat.py` |
| Used in duel | `backend/app/ws/duel.py` |
| Frontend telemetry hook | `frontend/src/hooks/useTelemetry.js` |
