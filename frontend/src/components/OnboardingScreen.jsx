import { Link } from "react-router-dom";

export default function OnboardingScreen() {
  return (
    <div className="onboarding-screen">
      <div className="onboarding-grid" />
      <div className="onboarding-glow" />

      <div className="onboarding-hero">
        <div className="onboarding-logo">
          <span className="onboarding-logo-accent">CP</span>
        </div>
        <h1 className="onboarding-title">CODEPANDEM</h1>
        <p className="onboarding-tagline">Compete. Code. Conquer.</p>
        <p className="onboarding-subtitle">
          Real-time competitive coding duels. Face opponents in escalating rounds,
          climb the ELO ladder, and prove your algorithmic skill.
        </p>

        <div className="onboarding-cta">
          <Link to="/register" className="onboarding-btn onboarding-btn-primary">
            Get Started
          </Link>
          <Link to="/login" className="onboarding-btn onboarding-btn-secondary">
            Sign In
          </Link>
        </div>
      </div>

      <div className="onboarding-features">
        <div className="onboarding-feature">
          <div className="onboarding-feature-icon">⚔️</div>
          <h3>1v1 Duels</h3>
          <p>Three escalating rounds against a live opponent. Easy to Hard.</p>
        </div>
        <div className="onboarding-feature">
          <div className="onboarding-feature-icon">🏆</div>
          <h3>Ranked Tiers</h3>
          <p>Bronze to Diamond. Every win pushes you up the ELO leaderboard.</p>
        </div>
        <div className="onboarding-feature">
          <div className="onboarding-feature-icon">🛡️</div>
          <h3>Fair Play</h3>
          <p>Anti-cheat telemetry keeps the competition honest and competitive.</p>
        </div>
        <div className="onboarding-feature">
          <div className="onboarding-feature-icon">📈</div>
          <h3>Seasons</h3>
          <p>Compete across ranked seasons with fresh leaderboards and stats.</p>
        </div>
      </div>

      <div className="onboarding-footer">
        <p>Built for coders who want to fight with logic.</p>
      </div>
    </div>
  );
}
