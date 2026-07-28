import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function validatePasswordLocal(password) {
  const checks = [
    { ok: password.length >= 8, label: "At least 8 characters" },
    { ok: /[A-Z]/.test(password), label: "One uppercase letter" },
    { ok: /[a-z]/.test(password), label: "One lowercase letter" },
    { ok: /[0-9]/.test(password), label: "One number" },
    { ok: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]/.test(password), label: "One special character" },
  ];
  return checks;
}

export default function RegisterScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [localError, setLocalError] = useState(null);
  const { register, loading, error } = useAuth();
  const navigate = useNavigate();

  const checks = validatePasswordLocal(password);
  const passwordValid = checks.every((c) => c.ok);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);
    if (!passwordValid) {
      setLocalError("Password does not meet requirements");
      return;
    }
    if (password !== confirm) {
      setLocalError("Passwords don't match");
      return;
    }
    try {
      await register(username, password);
      navigate("/");
    } catch {}
  };

  const displayError = localError || error;

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <h1 className="logo">CODEPANDEM</h1>
        <p className="auth-subtitle">Create your account</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <input
            type="text"
            placeholder="Username (3-30 chars)"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="auth-input"
            minLength={3}
            maxLength={30}
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
          <div className="password-requirements">
            {checks.map((c, i) => (
              <div key={i} className={`password-check ${c.ok ? "ok" : ""}`}>
                <span className="password-check-dot">{c.ok ? "✓" : "○"}</span>
                {c.label}
              </div>
            ))}
          </div>
          <input
            type="password"
            placeholder="Confirm password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className="auth-input"
            required
          />
          {displayError && <p className="auth-error">{displayError}</p>}
          <button
            type="submit"
            className="auth-btn"
            disabled={loading || !passwordValid}
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
