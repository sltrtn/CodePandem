import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user } = useAuth();

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand">CODEPANDEM</NavLink>
      <div className="navbar-links">
        <NavLink to="/" end className={({ isActive }) => `navbar-link ${isActive ? "active" : ""}`}>
          Battle
        </NavLink>
        <NavLink to="/leaderboard" className={({ isActive }) => `navbar-link ${isActive ? "active" : ""}`}>
          Leaderboard
        </NavLink>
        <NavLink to={`/profile/${user?.id}`} className={({ isActive }) => `navbar-link ${isActive ? "active" : ""}`}>
          Profile
        </NavLink>
      </div>
      <div className="navbar-user">
        <span className="navbar-username">{user?.username}</span>
        <span className={`tier-badge tier-${user?.tier}`}>{user?.tier}</span>
      </div>
    </nav>
  );
}
