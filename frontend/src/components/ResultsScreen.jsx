import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useDuel } from "../context/DuelContext";

const FLAG_LABELS = {
  speed: "Unusual Speed",
  paste: "Paste Detected",
  tabs: "Tab Switches",
  keystrokes: "Keystroke Anomaly",
  typing_pattern: "Unnatural Rhythm",
  plagiarism: "Code Similarity",
};

function CheatReport({ rounds, playerId }) {
  const [expanded, setExpanded] = useState(false);

  const allFlags = [];
  const playerScores = {};
  rounds.forEach((r) => {
    if (!r.players) return;
    Object.values(r.players).forEach((p) => {
      if (!playerScores[p.player_id]) {
        playerScores[p.player_id] = { total: 0, rounds: 0, flags: new Set() };
      }
      playerScores[p.player_id].total += p.cheat_score ?? 0;
      playerScores[p.player_id].rounds++;
      (p.cheat_flags || []).forEach((f) => {
        playerScores[p.player_id].flags.add(f);
        if (!allFlags.find((x) => x.flag === f && x.player_id === p.player_id)) {
          allFlags.push({ flag: f, player_id: p.player_id, round: r.round_number });
        }
      });
    });
  });

  if (allFlags.length === 0) return null;

  return (
    <div className="cheat-report">
      <button className="cheat-report-toggle" onClick={() => setExpanded(!expanded)}>
        <span className="cheat-report-icon">🛡</span>
        Integrity Report
        <span className={`cheat-report-arrow ${expanded ? "open" : ""}`}>▸</span>
      </button>
      {expanded && (
        <div className="cheat-report-body">
          {Object.entries(playerScores).map(([pid, data]) => (
            <div key={pid} className="cheat-report-player">
              <div className="cheat-report-player-header">
                <span>{pid === playerId ? "You" : "Opponent"}</span>
                <span className={`cheat-report-level ${data.total > 0.5 ? "high" : data.total > 0.3 ? "medium" : "low"}`}>
                  {(data.total / data.rounds).toFixed(2)} avg
                </span>
              </div>
              {data.flags.size > 0 && (
                <div className="cheat-report-flags">
                  {[...data.flags].map((f) => (
                    <span key={f} className="cheat-report-flag">
                      {FLAG_LABELS[f] || f}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ResultsScreen() {
  const { matchOver, playerId } = useDuel();
  const { token } = useAuth();
  const [rematchState, setRematchState] = useState(null);
  const [opponentReady, setOpponentReady] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!token || !matchOver?.match_id) return;

    const ws = new WebSocket(
      `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws/rematch/${matchOver.match_id}?token=${token}`
    );
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch (msg.type) {
        case "rematch_requested":
          if (msg.player_id !== playerId) {
            setOpponentReady(true);
          }
          break;
        case "rematch_accepted":
          setRematchState("accepted");
          break;
        case "rematch_cancelled":
          setRematchState(null);
          setOpponentReady(false);
          break;
      }
    };

    return () => ws.close();
  }, [token, matchOver?.match_id, playerId]);

  const handleRematch = () => {
    setRematchState("requested");
    wsRef.current?.send(JSON.stringify({ type: "request_rematch" }));
  };

  const handleCancel = () => {
    setRematchState(null);
    setOpponentReady(false);
    wsRef.current?.send(JSON.stringify({ type: "cancel_rematch" }));
  };

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

        <CheatReport rounds={rounds} playerId={playerId} />

        <div className="results-actions">
          {!rematchState ? (
            <button className="results-rematch-btn" onClick={handleRematch}>
              Request Rematch
            </button>
          ) : rematchState === "requested" ? (
            <div className="results-rematch-pending">
              <span className="results-spinner" />
              Waiting for opponent...
              {opponentReady && (
                <span className="results-accepting">Opponent ready!</span>
              )}
              <button className="results-cancel-btn" onClick={handleCancel}>
                Cancel
              </button>
            </div>
          ) : (
            <div className="results-rematch-accepted">
              <span className="results-check" />
              Rematch accepted!
            </div>
          )}

          <Link to="/lobby" className="results-lobby-btn">
            Back to Lobby
          </Link>
          <Link to="/" className="results-back-btn">
            Back to Queue
          </Link>
        </div>
      </div>
    </div>
  );
}
