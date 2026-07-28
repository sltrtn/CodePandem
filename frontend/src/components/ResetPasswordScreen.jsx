import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function validatePassword(password) {
  const checks = [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[a-z]/.test(password),
    /[0-9]/.test(password),
    /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]/.test(password),
  ];
  return checks.every(Boolean);
}

export default function ResetPasswordScreen() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [status, setStatus] = useState(null);
  const { confirmPasswordReset } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus(null);
    if (!validatePassword(password)) {
      setStatus("Password does not meet requirements");
      return;
    }
    if (password !== confirm) {
      setStatus("Passwords don't match");
      return;
    }
    try {
      await confirmPasswordReset(token, password);
      setStatus("Password reset. Redirecting to login...");
      setTimeout(() => navigate("/login"), 1500);
    } catch (e) {
      setStatus(e.message);
    }
  };

  if (!token) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <h1 className="logo">CODEPANDEM</h1>
          <p className="auth-error">Invalid reset link.</p>
          <p className="auth-switch">
            <Link to="/login">Back to login</Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <h1 className="logo">CODEPANDEM</h1>
        <p className="auth-subtitle">Set a new password</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <input
            type="password"
            placeholder="New password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="auth-input"
            required
          />
          <input
            type="password"
            placeholder="Confirm password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className="auth-input"
            required
          />
          {status && <p className="auth-error">{status}</p>}
          <button type="submit" className="auth-btn">
            Reset Password
          </button>
        </form>
        <p className="auth-switch">
          <Link to="/login">Back to login</Link>
        </p>
      </div>
    </div>
  );
}
