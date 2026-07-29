import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function CustomLobbyScreen() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [createdCode, setCreatedCode] = useState(null);
  const [joining, setJoining] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const api = "/api";

  const handleCreate = async () => {
    setCreating(true);
    setError(null);
    const res = await fetch(`${api}/social/lobby/create`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const data = await res.json();
      setCreatedCode(data.code);
    } else {
      setError("Failed to create lobby");
    }
    setCreating(false);
  };

  const handleJoin = async () => {
    if (!code.trim()) return;
    setJoining(true);
    setError(null);
    const res = await fetch(`${api}/social/lobby/join/${code.trim()}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const data = await res.json();
      navigate(`/duel/${data.match_id}`);
    } else {
      const err = await res.json();
      setError(err.detail || "Failed to join lobby");
    }
    setJoining(false);
  };

  return (
    <div className="custom-lobby-screen">
      <div className="custom-lobby-card">
        <h2 className="custom-lobby-title">Custom Game</h2>

        <div className="custom-lobby-section">
          <h3>Create a Lobby</h3>
          <p className="custom-lobby-desc">
            Create a private lobby and share the code with a friend
          </p>
          <button
            className="custom-lobby-create-btn"
            onClick={handleCreate}
            disabled={creating}
          >
            {creating ? "Creating..." : "Create Lobby"}
          </button>
          {createdCode && (
            <div className="custom-lobby-code">
              <span className="custom-lobby-code-label">Share this code:</span>
              <span className="custom-lobby-code-value">{createdCode}</span>
              <button
                className="custom-lobby-copy-btn"
                onClick={() => {
                  navigator.clipboard.writeText(createdCode);
                }}
              >
                Copy
              </button>
            </div>
          )}
        </div>

        <div className="custom-lobby-divider">
          <span>OR</span>
        </div>

        <div className="custom-lobby-section">
          <h3>Join a Lobby</h3>
          <p className="custom-lobby-desc">
            Enter the 6-character code from the host
          </p>
          <div className="custom-lobby-join-row">
            <input
              className="custom-lobby-input"
              type="text"
              placeholder="e.g. ABC123"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              maxLength={6}
            />
            <button
              className="custom-lobby-join-btn"
              onClick={handleJoin}
              disabled={joining || !code.trim()}
            >
              {joining ? "Joining..." : "Join"}
            </button>
          </div>
        </div>

        {error && <div className="custom-lobby-error">{error}</div>}
      </div>
    </div>
  );
}
