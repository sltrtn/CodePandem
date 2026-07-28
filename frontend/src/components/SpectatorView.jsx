import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function CheatMeter({ score, breakdown }) {
  const level = score > 0.5 ? "high" : score > 0.3 ? "medium" : "low";
  return (
    <div className="spec-cheat-meter">
      <div className="spec-cheat-bar">
        <div className={`spec-cheat-fill ${level}`} style={{ width: `${Math.max(5, score * 100)}%` }} />
      </div>
      <span className={`spec-cheat-label ${level}`}>{(score * 100).toFixed(0)}%</span>
      {breakdown && Object.keys(breakdown).length > 0 && (
        <div className="spec-cheat-breakdown">
          {Object.entries(breakdown).map(([key, val]) => (
            <span key={key} className={`spec-cheat-signal ${val > 0.2 ? "active" : ""}`}>
              {key.replace("_", " ")}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SpectatorView() {
  const { matchId } = useParams();
  const { token } = useAuth();
  const [state, setState] = useState(null);
  const [code, setCode] = useState({ p1: "", p2: "" });
  const [cheatScores, setCheatScores] = useState({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!token || !matchId) return;

    const ws = new WebSocket(
      `ws://localhost:8000/ws/spectate/${matchId}?token=${token}`
    );
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch (msg.type) {
        case "spectate_state":
          setState(msg);
          break;
        case "duel_state":
          setState((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              current_round: msg.current_round,
              round: msg.round || prev.round,
              players: msg.players || prev.players,
            };
          });
          if (msg.submission_result) {
            const pid = msg.player_id;
            setCheatScores((prev) => ({
              ...prev,
              [pid]: {
                score: msg.submission_result.cheat_score ?? 0,
                breakdown: msg.submission_result.cheat_breakdown ?? {},
              },
            }));
          }
          break;
        case "round_start":
          setState((prev) => ({
            ...prev,
            current_round: msg.round?.round_number || msg.round_number,
            status: "active",
            round: msg.round || {
              round_number: msg.round_number,
              problem: msg.problem,
              time_limit_s: msg.time_limit_s,
            },
          }));
          setCode({ p1: "", p2: "" });
          setCheatScores({});
          break;
        case "round_over":
          setState((prev) => ({
            ...prev,
            round: msg.round || prev.round,
            players: msg.players || prev.players,
          }));
          break;
        case "match_over":
          setState((prev) => ({
            ...prev,
            status: "completed",
            winner: msg.winner,
            match_result: msg,
          }));
          break;
      }
    };

    return () => ws.close();
  }, [token, matchId]);

  if (!connected) {
    return (
      <div className="spectator-screen">
        <div className="spectator-connecting">Connecting to match...</div>
      </div>
    );
  }

  if (!state) {
    return (
      <div className="spectator-screen">
        <div className="spectator-connecting">Loading match state...</div>
      </div>
    );
  }

  const problem = state.round?.problem;
  const p1 = state.players ? Object.values(state.players)[0] : null;
  const p2 = state.players ? Object.values(state.players)[1] : null;

  return (
    <div className="spectator-screen">
      <div className="spectator-header">
        <div className="spectator-badge">LIVE SPECTATING</div>
        <div className="spectator-match-id">Match: {matchId.slice(0, 8)}...</div>
        <Link to="/lobby" className="spectator-leave">
          Leave
        </Link>
      </div>

      <div className="spectator-scoreboard">
        <div className={`spectator-player-card ${state.winner === p1?.player_id ? "winner" : ""}`}>
          <div className="spectator-avatar">{p1?.username?.[0]?.toUpperCase() || "?"}</div>
          <div className="spectator-player-info">
            <div className="spectator-name">{p1?.username || "Unknown"}</div>
            <div className="spectator-wins">Wins: {p1?.round_wins || 0}</div>
          </div>
          <div className="spectator-score">{(p1?.total_score || 0).toFixed(2)}</div>
          <CheatMeter
            score={cheatScores[p1?.player_id]?.score ?? 0}
            breakdown={cheatScores[p1?.player_id]?.breakdown ?? {}}
          />
        </div>

        <div className="spectator-vs">VS</div>

        <div className={`spectator-player-card ${state.winner === p2?.player_id ? "winner" : ""}`}>
          <div className="spectator-avatar">{p2?.username?.[0]?.toUpperCase() || "?"}</div>
          <div className="spectator-player-info">
            <div className="spectator-name">{p2?.username || "Unknown"}</div>
            <div className="spectator-wins">Wins: {p2?.round_wins || 0}</div>
          </div>
          <div className="spectator-score">{(p2?.total_score || 0).toFixed(2)}</div>
          <CheatMeter
            score={cheatScores[p2?.player_id]?.score ?? 0}
            breakdown={cheatScores[p2?.player_id]?.breakdown ?? {}}
          />
        </div>
      </div>

      {state.round?.problem && (
        <div className="spectator-problem">
          <div className="spectator-problem-header">
            <span className="spectator-round">
              Round {state.current_round} — {problem.difficulty}
            </span>
            <span className="spectator-time">{state.round.time_limit_s || state.round.time_limit}s</span>
          </div>
          <h3>{problem.title}</h3>
          <p className="spectator-problem-desc">{problem.description}</p>
        </div>
      )}

      {state.status === "completed" && (
        <div className="spectator-result">
          <h2>Match Over — {state.players[state.winner]?.username} wins!</h2>
          <p>3-round match concluded</p>
          <Link to="/lobby" className="spectator-back">
            Back to Lobby
          </Link>
        </div>
      )}

      <div className="spectator-code-panels">
        <div className="spectator-panel">
          <h4>{p1?.username || "Player 1"}</h4>
          <textarea
            className="spectator-code"
            value={code.p1}
            readOnly
            placeholder="Code will appear here..."
          />
        </div>
        <div className="spectator-panel">
          <h4>{p2?.username || "Player 2"}</h4>
          <textarea
            className="spectator-code"
            value={code.p2}
            readOnly
            placeholder="Code will appear here..."
          />
        </div>
      </div>
    </div>
  );
}
