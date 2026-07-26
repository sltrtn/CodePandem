import { useDuel } from "../context/DuelContext";

export default function ResultsScreen() {
  const { matchOver, playerId } = useDuel();
  if (!matchOver) return null;

  const isWinner = matchOver.winner === playerId;
  const entries = Object.values(matchOver.players || {});
  const rounds = matchOver.rounds || [];

  return (
    <div className="results-screen">
      <div className="results-card">
        <h1 className={`results-title ${isWinner ? "win" : "lose"}`}>
          {isWinner ? "VICTORY" : "DEFEAT"}
        </h1>
        <div className="results-score">
          {entries.map((p) => (
            <div key={p.player_id} className="results-player">
              <span>{p.player_id === playerId ? "You" : "Opponent"}</span>
              <span className="results-wins">{p.round_wins}</span>
            </div>
          ))}
        </div>

        <div className="results-rounds">
          {rounds.map((r, i) => (
            <div key={i} className="results-round-row">
              <span className="results-round-num">R{r.round_number}</span>
              <span className="results-round-diff">{r.problem?.difficulty}</span>
              <span className="results-round-winner">
                {r.winner === playerId ? "Won" : r.winner ? "Lost" : "Draw"}
              </span>
            </div>
          ))}
        </div>

        <a href="/" className="results-back-btn">
          Back to Queue
        </a>
      </div>
    </div>
  );
}
