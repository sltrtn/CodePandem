import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const API = "http://localhost:8000";

export default function LeaderboardScreen() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [season, setSeason] = useState("current");
  const [seasonName, setSeasonName] = useState("Current Season");
  const { user, token } = useAuth();

  useEffect(() => {
    setLoading(true);
    const headers = token ? { Authorization: `Bearer ${token}` } : {};

    const requests = [
      fetch(`${API}/auth/leaderboard?season=${season}&limit=50`, { headers }).then(
        (r) => r.json()
      ),
    ];
    if (season === "current") {
      requests.push(
        fetch(`${API}/seasons/current`, { headers }).then((r) => r.json())
      );
    }

    Promise.all(requests)
      .then(([data, seasonData]) => {
        setPlayers(data);
        if (seasonData?.name) {
          setSeasonName(seasonData.name);
        } else {
          setSeasonName("All Time");
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [season, token]);

  if (loading) return <div className="loading">Loading leaderboard...</div>;

  return (
    <div className="leaderboard-screen">
      <div className="leaderboard-card">
        <h2 className="leaderboard-title">Leaderboard</h2>
        <p className="leaderboard-subtitle">{seasonName}</p>

        <div className="leaderboard-toggle">
          <button
            className={`leaderboard-toggle-btn ${season === "current" ? "active" : ""}`}
            onClick={() => setSeason("current")}
          >
            Current Season
          </button>
          <button
            className={`leaderboard-toggle-btn ${season === "alltime" ? "active" : ""}`}
            onClick={() => setSeason("alltime")}
          >
            All Time
          </button>
        </div>

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
