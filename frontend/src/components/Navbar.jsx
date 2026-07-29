import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user } = useAuth();

  const firstLetter = user?.username?.[0]?.toUpperCase() || "?";

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <NavLink to="/" className="navbar-brand">
          <span className="navbar-brand-mark">CP</span>
          <span className="navbar-brand-text">CODEPANDEM</span>
        </NavLink>
      </div>

      <div className="navbar-center">
        <NavLink to="/" end className={({ isActive }) => `navbar-link ${isActive ? "active" : ""}`}>
          Battle
        </NavLink>
        <NavLink to="/leaderboard" className={({ isActive }) => `navbar-link ${isActive ? "active" : ""}`}>
          Leaderboard
        </NavLink>
        <NavLink to={`/profile/${user?.id}`} className={({ isActive }) => `navbar-link ${isActive ? "active" : ""}`}>
          Profile
        </NavLink>
        <div className="navbar-divider" />
        <NavLink to="/lobby" className={({ isActive }) => `navbar-link secondary ${isActive ? "active" : ""}`}>
          Lobby
        </NavLink>
        <NavLink to="/friends" className={({ isActive }) => `navbar-link secondary ${isActive ? "active" : ""}`}>
          Friends
        </NavLink>
        <NavLink to="/custom-game" className={({ isActive }) => `navbar-link secondary ${isActive ? "active" : ""}`}>
          Custom
        </NavLink>
      </div>

      <div className="navbar-right">
        <div className="navbar-user">
          <span className={`tier-badge tier-${user?.tier}`}>{user?.tier}</span>
          <span className="navbar-username">{user?.username}</span>
          <span className="navbar-avatar">{firstLetter}</span>
        </div>
      </div>
    </nav>
  );
}
