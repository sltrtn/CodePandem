import { useDuel } from "../context/DuelContext";

export default function RoundIndicator() {
  const { matchState, playerId } = useDuel();
  if (!matchState) return null;

  const round = matchState.current_round;
  const total = 3;

  return (
    <div className="round-indicator">
      <div className="round-dots">
        {Array.from({ length: total }, (_, i) => (
          <div
            key={i}
            className={`round-dot ${i + 1 === round ? "active" : ""} ${
              matchState.players?.[playerId]?.round_wins > i ? "won" : ""
            }`}
          />
        ))}
      </div>
      <span className="round-label">
        Round {round} of {total}
      </span>
    </div>
  );
}
