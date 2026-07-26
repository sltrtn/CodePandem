import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function QueueScreen() {
  const [status, setStatus] = useState("connecting");
  const [position, setPosition] = useState(0);
  const { token } = useAuth();
  const wsRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/queue?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      ws.send(JSON.stringify({ type: "join_queue" }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "queued") {
        setPosition(msg.position);
        localStorage.setItem("playerId", msg.player_id);
      } else if (msg.type === "match_found") {
        localStorage.setItem("playerId", msg.player_id);
        navigate(`/duel/${msg.match_id}`);
      }
    };

    ws.onclose = () => setStatus("disconnected");
    ws.onerror = () => setStatus("error");

    return () => ws.close();
  }, [token, navigate]);

  return (
    <div className="queue-screen">
      <div className="queue-card">
        <h1 className="logo">CODEPANDEM</h1>
        <div className="queue-status">
          {status === "connecting" && <p>Connecting...</p>}
          {status === "error" && <p className="error">Connection failed. Is the server running?</p>}
          {status === "disconnected" && <p className="error">Disconnected.</p>}
          {status === "connected" && (
            <>
              <div className="spinner" />
              <p className="queue-text">Searching for opponent...</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
