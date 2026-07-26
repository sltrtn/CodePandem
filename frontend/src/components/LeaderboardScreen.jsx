import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const API = "http://localhost:8000";

export default function LeaderboardScreen() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetch(`${API}/auth/leaderboard?limit=50`)
      .then((r) => r.json())
      .then((data) => {
        setPlayers(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading leaderboard...</div>;

  return (
    <div className="leaderboard-screen">
      <div className="leaderboard-card">
        <h2 className="leaderboard-title">Leaderboard</h2>
        <p className="leaderboard-subtitle">Top fighters by ELO rating</p>
        <div className="leaderboard-list">
          {players.map((p, i) => (
            <Link
              to={`/profile/${p.id}`}
              key={p.id}
              className={`leaderboard-row ${p.id === user?.id ? "me" : ""}`}
            >
              <span className="leaderboard-rank">{i + 1}</span>
              <div className="leaderboard-info">
                <span className="leaderboard-name">{p.username}</span>
                <span className={`tier-badge tier-${p.tier}`}>{p.tier}</span>
              </div>
              <div className="leaderboard-stats">
                <span className="leaderboard-elo">{p.elo}</span>
                <span className="leaderboard-record">
                  {p.wins}W {p.losses}L {p.draws}D
                </span>
              </div>
            </Link>
          ))}
          {players.length === 0 && (
            <p className="leaderboard-empty">No players yet. Be the first!</p>
          )}
        </div>
      </div>
    </div>
  );
}
