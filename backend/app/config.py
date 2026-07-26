from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    SUBMISSION_TIMEOUT_S: int = 5
    MEMORY_LIMIT_MB: int = 128

    ROUNDS_PER_MATCH: int = 3
    ROUND_TIMES: list[int] = field(default_factory=lambda: [180, 300, 480])
    ROUND_DIFFICULTIES: list[str] = field(default_factory=lambda: ["easy", "medium", "hard"])

    WINS_NEEDED: int = 2

    ANTI_CHEAT_SPEED_THRESHOLDS: dict[str, int] = field(
        default_factory=lambda: {"easy": 8, "medium": 15, "hard": 25}
    )
    ANTI_CHEAT_PASTE_LENGTH_MIN: int = 50
    ANTI_CHEAT_TAB_TIME_SUSPICIOUS_MS: int = 30_000
    ANTI_CHEAT_FLAG_THRESHOLD: float = 0.5
    ANTI_CHEAT_WARN_THRESHOLD: float = 0.3


CONFIG = Config()
