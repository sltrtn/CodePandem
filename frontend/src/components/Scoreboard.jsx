import { useDuel } from "../context/DuelContext";

export default function Scoreboard() {
  const { players, playerId, matchState } = useDuel();

  const entries = Object.values(players);

  return (
    <div className="scoreboard">
      <h3 className="scoreboard-title">Scoreboard</h3>
      {entries.map((p) => {
        const isMe = p.player_id === playerId;
        return (
          <div key={p.player_id} className={`scoreboard-row ${isMe ? "me" : ""}`}>
            <div className="scoreboard-name">
              {isMe ? "You" : "Opponent"}
              {p.suspicious && <span className="cheat-flag" title="Suspicious activity detected"> ⚠</span>}
            </div>
            <div className="scoreboard-stats">
              <div className="stat">
                <span className="stat-label">Wins</span>
                <span className="stat-value">{p.round_wins ?? 0}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Score</span>
                <span className="stat-value">{(p.total_score ?? 0).toFixed(2)}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
