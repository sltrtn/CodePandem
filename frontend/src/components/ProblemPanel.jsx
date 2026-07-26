import { useDuel } from "../context/DuelContext";

export default function ProblemPanel() {
  const { roundData } = useDuel();
  if (!roundData?.problem) return null;

  const { problem } = roundData;
  const diffColor = { easy: "#4ade80", medium: "#facc15", hard: "#f87171" };

  return (
    <div className="problem-panel">
      <div className="problem-header">
        <h2 className="problem-title">{problem.title}</h2>
        <span
          className="problem-difficulty"
          style={{ color: diffColor[problem.difficulty] || "#aaa" }}
        >
          {problem.difficulty}
        </span>
      </div>
      <pre className="problem-description">{problem.description}</pre>
    </div>
  );
}
