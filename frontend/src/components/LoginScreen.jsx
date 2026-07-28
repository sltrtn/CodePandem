import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showReset, setShowReset] = useState(false);
  const [resetUsername, setResetUsername] = useState("");
  const [resetStatus, setResetStatus] = useState(null);
  const { login, requestPasswordReset, loading, error } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(username, password);
      navigate("/");
    } catch {}
  };

  const handleReset = async (e) => {
    e.preventDefault();
    setResetStatus(null);
    try {
      const data = await requestPasswordReset(resetUsername);
      setResetStatus({ type: "success", message: "Reset link sent if account exists." });
      // In dev mode, show the token
      if (data.token) {
        setResetStatus({
          type: "dev",
          message: `Dev token: ${data.token}`,
        });
      }
    } catch (e) {
      setResetStatus({ type: "error", message: e.message });
    }
  };

  if (showReset) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <h1 className="logo">CODEPANDEM</h1>
          <p className="auth-subtitle">Reset your password</p>
          <form onSubmit={handleReset} className="auth-form">
            <input
              type="text"
              placeholder="Username"
              value={resetUsername}
              onChange={(e) => setResetUsername(e.target.value)}
              className="auth-input"
              required
            />
            {resetStatus && (
              <p className={`auth-status ${resetStatus.type}`}>
                {resetStatus.message}
              </p>
            )}
            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? "Sending..." : "Send Reset Link"}
            </button>
          </form>
          <p className="auth-switch">
            <button className="auth-link-btn" onClick={() => setShowReset(false)}>
              Back to sign in
            </button>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <h1 className="logo">CODEPANDEM</h1>
        <p className="auth-subtitle">Sign in to battle</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="auth-input"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="auth-input"
            required
          />
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        <p className="auth-switch">
          <button className="auth-link-btn" onClick={() => setShowReset(true)}>
            Forgot password?
          </button>
        </p>
        <p className="auth-switch">
          Don't have an account? <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}
