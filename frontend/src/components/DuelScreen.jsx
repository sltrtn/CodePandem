import { useDuel } from "../context/DuelContext";
import CodeEditor from "./CodeEditor";
import Scoreboard from "./Scoreboard";
import ProblemPanel from "./ProblemPanel";
import RoundIndicator from "./RoundIndicator";
import ResultsScreen from "./ResultsScreen";
import CountdownTimer from "./CountdownTimer";
import ChatPanel from "./ChatPanel";

export default function DuelScreen() {
  const { matchOver, roundData, roundOver, playerId } = useDuel();

  if (matchOver) return <ResultsScreen />;
  if (!roundData) return <div className="loading">Loading match...</div>;

  const roundWinnerText = !roundOver?.winner
    ? "Draw"
    : roundOver.winner === playerId
    ? "You"
    : "Opponent";

  return (
    <div className="duel-screen">
      <RoundIndicator />
      <div className="duel-timer">
        <CountdownTimer />
      </div>
      {roundOver && !matchOver && (
        <div className="round-overlay">
          <div className="round-result-card">
            <h2>Round {roundOver.round_number} Complete</h2>
            <p>
              Winner: <strong>{roundWinnerText}</strong>
            </p>
          </div>
        </div>
      )}
      <div className="duel-layout">
        <div className="duel-left">
          <ProblemPanel />
          <CodeEditor />
        </div>
        <div className="duel-right">
          <Scoreboard />
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}
