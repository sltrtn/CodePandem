from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from fastapi import WebSocket


@dataclass
class Telemetry:
    paste_events: list[dict] = field(default_factory=list)
    tab_switches: list[dict] = field(default_factory=list)
    keystroke_count: int = 0
    keystrokes_per_second: float = 0.0
    time_since_match_start_ms: int = 0
    paste_event_count: int = 0
    total_paste_length: int = 0
    tab_switch_count: int = 0
    total_tab_time_ms: int = 0


@dataclass
class SubmissionResult:
    test_cases_passed: int = 0
    test_cases_total: int = 0
    time_ms: float = 0.0
    memory_kb: float = 0.0
    output: str = ""
    error: str | None = None
    cheat_score: float = 0.0
    cheat_flags: list[str] = field(default_factory=list)
    suspicious: bool = False


@dataclass
class CheatScore:
    composite: float = 0.0
    breakdown: dict[str, float] = field(default_factory=dict)
    flagged: bool = False
    suspicious: bool = False


@dataclass
class Problem:
    id: str = ""
    title: str = ""
    description: str = ""
    difficulty: str = "easy"
    test_cases: list[dict] = field(default_factory=list)


@dataclass
class PlayerRoundState:
    player_id: str = ""
    score: float = 0.0
    submissions: int = 0
    last_result: SubmissionResult | None = None
    total_time_ms: float = 0.0


@dataclass
class Round:
    round_number: int = 1
    problem: Problem = field(default_factory=Problem)
    time_limit_s: int = 180
    status: str = "active"
    winner: str | None = None
    players: dict[str, PlayerRoundState] = field(default_factory=dict)


@dataclass
class PlayerState:
    player_id: str = ""
    ws: WebSocket | None = None
    total_score: float = 0.0
    round_wins: int = 0
    rounds_played: int = 0


@dataclass
class Match:
    match_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    players: dict[str, PlayerState] = field(default_factory=dict)
    rounds: list[Round] = field(default_factory=list)
    current_round: int = 0
    status: str = "waiting"
    winner: str | None = None

    def add_player(self, ws: WebSocket) -> str:
        pid = uuid.uuid4().hex[:8]
        self.players[pid] = PlayerState(player_id=pid, ws=ws)
        return pid

    def get_opponent_id(self, player_id: str) -> str | None:
        for pid in self.players:
            if pid != player_id:
                return pid
        return None
