import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

const API = "http://localhost:8000";

export default function ProfileScreen() {
  const { userId } = useParams();
  const [profile, setProfile] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);

  // Easter egg — tap name 7 times
  const [easterEggTaps, setEasterEggTaps] = useState(0);
  const [showSlater, setShowSlater] = useState(false);

  useEffect(() => {
    setEasterEggTaps(0);
    setShowSlater(false);
  }, [userId]);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API}/auth/users/${userId}`).then((r) => r.json()),
      fetch(`${API}/auth/users/${userId}/matches?limit=20`).then((r) => r.json()),
    ])
      .then(([profileData, matchData]) => {
        setProfile(profileData);
        setMatches(matchData);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [userId]);

  if (loading) return <div className="loading">Loading profile...</div>;
  if (!profile?.id) return <div className="loading">User not found</div>;

  const winRate = profile.games_played > 0
    ? Math.round((profile.wins / profile.games_played) * 100)
    : 0;

  return (
    <div className="profile-screen">
      <div className="profile-card">
        <div className="profile-header">
          <div className="profile-avatar">{profile.username[0].toUpperCase()}</div>
          <div className="profile-identity">
            <h2
              className="profile-name"
              onClick={() => {
                setEasterEggTaps((t) => {
                  const next = t + 1;
                  if (next >= 7) setShowSlater(true);
                  return next;
                });
              }}
              style={{ cursor: "pointer" }}
            >
              {profile.username}
            </h2>
            <span className={`tier-badge tier-${profile.tier}`}>{profile.tier}</span>
            {!showSlater && easterEggTaps > 0 && easterEggTaps < 7 && (
              <span className="easter-egg-hint">{7 - easterEggTaps} more...</span>
            )}
          </div>
        </div>

        {showSlater && (
          <a
            href="https://github.com/sltrtn"
            target="_blank"
            rel="noopener noreferrer"
            className="slater-card"
          >
            <span className="slater-name">Slater</span>
            <span className="slater-tagline">The one who started it all.</span>
            <span className="slater-link">github.com/sltrtn</span>
          </a>
        )}

        <div className="profile-stats-grid">
          <div className="profile-stat">
            <span className="profile-stat-value">{profile.elo}</span>
            <span className="profile-stat-label">ELO</span>
          </div>
          <div className="profile-stat">
            <span className="profile-stat-value">{profile.games_played}</span>
            <span className="profile-stat-label">Games</span>
          </div>
          <div className="profile-stat">
            <span className="profile-stat-value win-color">{profile.wins}</span>
            <span className="profile-stat-label">Wins</span>
          </div>
          <div className="profile-stat">
            <span className="profile-stat-value loss-color">{profile.losses}</span>
            <span className="profile-stat-label">Losses</span>
          </div>
          <div className="profile-stat">
            <span className="profile-stat-value">{profile.draws}</span>
            <span className="profile-stat-label">Draws</span>
          </div>
          <div className="profile-stat">
            <span className="profile-stat-value">{winRate}%</span>
            <span className="profile-stat-label">Win Rate</span>
          </div>
        </div>

        <div className="profile-section">
          <h3 className="profile-section-title">Match History</h3>
          {matches.length === 0 ? (
            <p className="profile-empty">No matches played yet</p>
          ) : (
            <div className="match-history">
              {matches.map((m) => {
                const isP1 = m.player1_id === userId;
                const opponent = isP1 ? m.player2_username : m.player1_username;
                const opponentId = isP1 ? m.player2_id : m.player1_id;
                const eloChange = isP1 ? m.player1_elo_change : m.player2_elo_change;
                const result = m.winner_id === userId ? "win" : m.winner_id ? "loss" : "draw";

                return (
                  <div key={m.id} className={`match-row match-${result}`}>
                    <div className="match-result-badge">{result.toUpperCase()}</div>
                    <div className="match-info">
                      <span className="match-opponent">
                        vs <Link to={`/profile/${opponentId}`}>{opponent}</Link>
                      </span>
                      <span className="match-meta">
                        {m.rounds_played} rounds &middot; {new Date(m.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <span className={`match-elo-change ${eloChange >= 0 ? "positive" : "negative"}`}>
                      {eloChange >= 0 ? "+" : ""}{eloChange}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
