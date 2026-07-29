import { useState } from "react";
import { useAuth } from "../context/AuthContext";

const steps = [
  {
    icon: "🎮",
    title: "Welcome to CodePandem",
    text: "A competitive arena where you face other developers in real-time coding duels. Fast thinking beats fast typing.",
  },
  {
    icon: "⚔️",
    title: "How Duels Work",
    text: "Each duel is a best-of-three match across Easy, Medium, and Hard problems. Solve faster and cleaner than your opponent to win the round.",
  },
  {
    icon: "🏆",
    title: "Climb the Ranks",
    text: "Your ELO changes after every duel. Climb from Bronze through Silver, Gold, Platinum, and Diamond. Every season resets the race.",
  },
  {
    icon: "🚀",
    title: "Your First Opponent Awaits",
    text: "Click Battle when you're ready. We'll find a fair match based on your rating. Good luck!",
  },
];

export default function TutorialOverlay() {
  const [step, setStep] = useState(0);
  const { apiRequest, updateUser } = useAuth();

  const handleNext = async () => {
    if (step === steps.length - 1) {
      try {
        await apiRequest("/auth/me/tutorial", { method: "PATCH" });
        updateUser({ tutorial_completed: true });
      } catch (e) {
        console.error("Failed to mark tutorial complete", e);
      }
    } else {
      setStep((s) => s + 1);
    }
  };

  return (
    <div className="tutorial-overlay">
      <div className="tutorial-backdrop" />
      <div className="tutorial-card">
        <div className="tutorial-step-number">
          Step {step + 1} of {steps.length}
        </div>
        <div className="tutorial-icon">{steps[step].icon}</div>
        <h2 className="tutorial-title">{steps[step].title}</h2>
        <p className="tutorial-text">{steps[step].text}</p>

        <div className="tutorial-dots">
          {steps.map((_, i) => (
            <span
              key={i}
              className={`tutorial-dot ${i === step ? "active" : ""}`}
            />
          ))}
        </div>

        <button className="tutorial-btn" onClick={handleNext}>
          {step === steps.length - 1 ? "Let's Go!" : "Next"}
        </button>
      </div>
    </div>
  );
}
