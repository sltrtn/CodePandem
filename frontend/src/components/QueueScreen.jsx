import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function QueueScreen() {
  const [status, setStatus] = useState("connecting");
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

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/queue?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "connected") {
        setStatus("connected");
        setQueueInfo((prev) => ({
          ...prev,
          elo: msg.elo ?? prev.elo,
          playersInQueue: msg.players_in_queue ?? prev.playersInQueue,
        }));
      } else if (msg.type === "queued") {
        setStatus("searching");
        setQueueInfo((prev) => ({
          ...prev,
          elo: msg.elo ?? prev.elo,
          playersInQueue: msg.position ?? prev.playersInQueue,
        }));
        if (!startTimeRef.current) {
          startTimeRef.current = Date.now();
          timerRef.current = setInterval(() => {
            setQueueInfo((prev) => ({
              ...prev,
              elapsed: Math.floor((Date.now() - startTimeRef.current) / 1000),
            }));
          }, 1000);
        }
      } else if (msg.type === "queue_status") {
        setQueueInfo((prev) => ({
          ...prev,
          range: msg.range ?? prev.range,
          playersInQueue: msg.players_in_queue ?? prev.playersInQueue,
          elo: msg.elo ?? prev.elo,
        }));
      } else if (msg.type === "left_queue") {
        setStatus("connected");
        setQueueInfo((prev) => ({ ...prev, elapsed: 0 }));
        if (timerRef.current) clearInterval(timerRef.current);
        startTimeRef.current = null;
      } else if (msg.type === "match_found") {
        localStorage.setItem("playerId", msg.player_id);
        navigate(`/duel/${msg.match_id}`);
      } else if (msg.type === "queue_timeout") {
        setStatus("timeout");
        if (timerRef.current) clearInterval(timerRef.current);
      }
    };

    ws.onclose = () => setStatus("disconnected");
    ws.onerror = () => setStatus("error");

    return () => {
      ws.close();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [token, navigate]);

  const handleBattle = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "join_queue", mode: "ranked" }));
      setStatus("searching");
      startTimeRef.current = Date.now();
      timerRef.current = setInterval(() => {
        setQueueInfo((prev) => ({
          ...prev,
          elapsed: Math.floor((Date.now() - startTimeRef.current) / 1000),
        }));
      }, 1000);
    }
  };

  const handleCancel = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "leave_queue" }));
    }
    setStatus("connected");
    setQueueInfo((prev) => ({ ...prev, elapsed: 0 }));
    if (timerRef.current) clearInterval(timerRef.current);
    startTimeRef.current = null;
  };

  const handleRetry = () => {
    setStatus("connected");
    setQueueInfo((prev) => ({ ...prev, elapsed: 0, range: 100 }));
    handleBattle();
  };

  const formatTime = (s) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="queue-screen">
      <div className="queue-card">
        <div className="queue-status-badge">
          {status === "connecting" && <span className="queue-status-dot pulse" />}
          {status === "connected" && <span className="queue-status-dot online" />}
          {status === "searching" && <span className="queue-status-dot pulse" />}
          {status === "timeout" && <span className="queue-status-dot offline" />}
          {status === "disconnected" && <span className="queue-status-dot offline" />}
          {status === "error" && <span className="queue-status-dot offline" />}
          <span className="queue-status-text">
            {status === "connecting" && "Connecting..."}
            {status === "connected" && "Connected"}
            {status === "searching" && "Searching..."}
            {status === "timeout" && "Timed out"}
            {status === "disconnected" && "Disconnected"}
            {status === "error" && "Connection error"}
          </span>
        </div>

        <h1 className="queue-title">
          {status === "connecting" && "Linking to Arena"}
          {status === "connected" && "Ready for Battle"}
          {status === "searching" && "Finding an Opponent"}
          {status === "timeout" && "No Match Found"}
          {status === "disconnected" && "Connection Lost"}
          {status === "error" && "Link Error"}
        </h1>

        {status === "connecting" && (
          <div className="queue-connecting">
            <div className="queue-spinner" />
            <p>Establishing secure arena connection...</p>
          </div>
        )}

        {status === "connected" && (
          <div className="queue-ready">
            <p className="queue-ready-text">
              The arena is live. {queueInfo.playersInQueue} player
              {queueInfo.playersInQueue === 1 ? "" : "s"} in queue.
            </p>
            <button className="queue-battle-btn" onClick={handleBattle}>
              <span className="queue-battle-icon">⚔️</span>
              <span>BATTLE</span>
            </button>
          </div>
        )}

        {status === "searching" && (
          <div className="queue-searching">
            <div className="queue-radar" />
            <div className="queue-stats">
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
            <button className="queue-cancel-btn" onClick={handleCancel}>
              Cancel
            </button>
          </div>
        )}

        {status === "timeout" && (
          <div className="queue-timeout">
            <p>We could not find a suitable opponent right now.</p>
            <button className="queue-battle-btn" onClick={handleRetry}>
              Try Again
            </button>
          </div>
        )}

        {(status === "disconnected" || status === "error") && (
          <div className="queue-error">
            <p>Lost connection to the arena. Refresh the page to reconnect.</p>
          </div>
        )}
      </div>
    </div>
  );
}
