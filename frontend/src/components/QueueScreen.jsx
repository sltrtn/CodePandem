import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function QueueScreen() {
  const [status, setStatus] = useState("connecting");
  const [mode, setMode] = useState("ranked");
  const [queueInfo, setQueueInfo] = useState({
    elapsed: 0,
    range: 100,
    playersInQueue: 0,
    elo: 1000,
  });
  const { token, user } = useAuth();
  const wsRef = useRef(null);
  const navigate = useNavigate();
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);

  useEffect(() => {
    if (!token) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/queue?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      ws.send(JSON.stringify({ type: "join_queue", mode }));
      startTimeRef.current = Date.now();
      timerRef.current = setInterval(() => {
        if (startTimeRef.current) {
          setQueueInfo((prev) => ({
            ...prev,
            elapsed: Math.floor((Date.now() - startTimeRef.current) / 1000),
          }));
        }
      }, 1000);
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "queued") {
        setQueueInfo((prev) => ({
          ...prev,
          elo: msg.elo ?? prev.elo,
          playersInQueue: msg.position ?? prev.playersInQueue,
        }));
      } else if (msg.type === "queue_status") {
        setQueueInfo((prev) => ({
          ...prev,
          range: msg.range ?? prev.range,
          playersInQueue: msg.players_in_queue ?? prev.playersInQueue,
          elo: msg.elo ?? prev.elo,
        }));
      } else if (msg.type === "match_found") {
        localStorage.setItem("playerId", msg.player_id);
        navigate(`/duel/${msg.match_id}`);
      } else if (msg.type === "queue_timeout") {
        setStatus("timeout");
      }
    };

    ws.onclose = () => setStatus("disconnected");
    ws.onerror = () => setStatus("error");

    return () => {
      ws.close();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [token, navigate, mode]);

  const formatTime = (s) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="queue-screen">
      <div className="queue-card">
        <h1 className="logo">CODEPANDEM</h1>

        <div className="queue-mode-toggle">
          <button
            className={`queue-mode-btn ${mode === "ranked" ? "active" : ""}`}
            onClick={() => setMode("ranked")}
            disabled={status === "connected"}
          >
            Ranked
          </button>
          <button
            className={`queue-mode-btn ${mode === "unranked" ? "active" : ""}`}
            onClick={() => setMode("unranked")}
            disabled={status === "connected"}
          >
            Unranked
          </button>
        </div>

        <div className="queue-status">
          {status === "connecting" && <p>Connecting...</p>}
          {status === "error" && <p className="error">Connection failed. Is the server running?</p>}
          {status === "disconnected" && <p className="error">Disconnected.</p>}
          {status === "timeout" && <p className="error">Queue timed out. Try again.</p>}
          {status === "connected" && (
            <>
              <div className="spinner" />
              <p className="queue-text">Searching for opponent...</p>
              <div className="queue-stats">
                <div className="queue-stat">
                  <span className="queue-stat-label">Mode</span>
                  <span className="queue-stat-value">{mode}</span>
                </div>
                <div className="queue-stat">
                  <span className="queue-stat-label">ELO</span>
                  <span className="queue-stat-value">{queueInfo.elo}</span>
                </div>
                <div className="queue-stat">
                  <span className="queue-stat-label">Range</span>
                  <span className="queue-stat-value">±{queueInfo.range}</span>
                </div>
                <div className="queue-stat">
                  <span className="queue-stat-label">Wait</span>
                  <span className="queue-stat-value">{formatTime(queueInfo.elapsed)}</span>
                </div>
                <div className="queue-stat">
                  <span className="queue-stat-label">In Queue</span>
                  <span className="queue-stat-value">{queueInfo.playersInQueue}</span>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
