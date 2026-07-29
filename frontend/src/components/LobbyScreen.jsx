import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useChallenge } from "../context/ChallengeContext";

export default function LobbyScreen() {
  const { token, user } = useAuth();
  const { sendChallenge } = useChallenge();
  const [players, setPlayers] = useState([]);
  const [activeMatches, setActiveMatches] = useState([]);
  const [onlineCount, setOnlineCount] = useState(0);
  const wsRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) return;

    const ws = new WebSocket(`${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws/lobby?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "get_players" }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch (msg.type) {
        case "lobby_state":
          setPlayers(msg.players || []);
          setActiveMatches(msg.active_matches || []);
          setOnlineCount(msg.players?.length || 0);
          break;
        case "player_joined":
          setPlayers((prev) => {
            if (prev.find((p) => p.player_id === msg.player.player_id)) return prev;
            return [...prev, msg.player];
          });
          setOnlineCount(msg.online_count);
          break;
        case "player_left":
          setPlayers((prev) => prev.filter((p) => p.player_id !== msg.player_id));
          setActiveMatches((prev) =>
            prev.filter((m) => m.player_id !== msg.player_id)
          );
          setOnlineCount(msg.online_count);
          break;
        case "player_status_changed":
          setPlayers((prev) =>
            prev.map((p) =>
              p.player_id === msg.player_id
                ? { ...p, status: msg.status, match_id: msg.match_id }
                : p
            )
          );
          if (msg.status === "in_match" && msg.match_id) {
            setActiveMatches((prev) => {
              if (prev.find((m) => m.match_id === msg.match_id)) return prev;
              const player = players.find((p) => p.player_id === msg.player_id);
              return [
                ...prev,
                {
                  match_id: msg.match_id,
                  player_id: msg.player_id,
                  username: player?.username || "Unknown",
                },
              ];
            });
          } else if (msg.status === "online") {
            setActiveMatches((prev) =>
              prev.filter((m) => m.player_id !== msg.player_id)
            );
          }
          setOnlineCount(msg.online_count);
          break;
      }
    };

    return () => ws.close();
  }, [token]);

  const handleWatch = (matchId) => {
    navigate(`/spectate/${matchId}`);
  };

  const handleChallenge = (e, playerId) => {
    e.preventDefault();
    e.stopPropagation();
    sendChallenge(playerId);
  };

  return (
    <div className="lobby-screen">
      <div className="lobby-card">
        <div className="lobby-header">
          <div>
            <h2 className="lobby-title">Lobby</h2>
            <p className="lobby-subtitle">
              {onlineCount} player{onlineCount !== 1 ? "s" : ""} online
            </p>
          </div>
          <Link to="/" className="lobby-queue-btn">
            Find Match
          </Link>
        </div>

        <div className="lobby-sections">
          <div className="lobby-section">
            <h3 className="lobby-section-title">Active Matches</h3>
            {activeMatches.length === 0 ? (
              <p className="lobby-empty">No active matches</p>
            ) : (
              <div className="lobby-match-list">
                {activeMatches.map((m) => (
                  <div key={m.match_id} className="lobby-match-row">
                    <div className="lobby-match-info">
                      <span className="lobby-match-id">
                        {m.match_id.slice(0, 8)}...
                      </span>
                      <span className="lobby-match-player">{m.username}</span>
                    </div>
                    <button
                      className="lobby-watch-btn"
                      onClick={() => handleWatch(m.match_id)}
                    >
                      Watch
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="lobby-section">
            <h3 className="lobby-section-title">Online Players</h3>
            {players.length === 0 ? (
              <p className="lobby-empty">No players online</p>
            ) : (
              <div className="lobby-player-list">
                {players.map((p) => (
                  <Link
                    to={`/profile/${p.player_id}`}
                    key={p.player_id}
                    className={`lobby-player-row ${p.player_id === user?.id ? "me" : ""}`}
                  >
                    <div className="lobby-player-avatar">
                      {p.username[0].toUpperCase()}
                    </div>
                    <div className="lobby-player-info">
                      <span className="lobby-player-name">{p.username}</span>
                      <span className="lobby-player-elo">
                        {p.elo} ELO
                      </span>
                    </div>
                    <div className="lobby-player-right">
                      <span className={`tier-badge tier-${p.tier}`}>{p.tier}</span>
                      {p.status === "online" && p.player_id !== user?.id && (
                        <button
                          className="lobby-challenge-btn"
                          onClick={(e) => handleChallenge(e, p.player_id)}
                        >
                          Challenge
                        </button>
                      )}
                      <span className={`lobby-status status-${p.status}`}>
                        {p.status === "online" && "Online"}
                        {p.status === "queued" && "In Queue"}
                        {p.status === "in_match" && "In Match"}
                        {p.status === "spectating" && "Spectating"}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
