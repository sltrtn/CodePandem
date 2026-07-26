import { useDuel } from "../context/DuelContext";

export default function CountdownTimer() {
  const { timerS } = useDuel();
  const mins = Math.floor(timerS / 60);
  const secs = timerS % 60;
  const isLow = timerS <= 30;

  return (
    <div className={`countdown-timer ${isLow ? "low" : ""}`}>
      {String(mins).padStart(2, "0")}:{String(secs).padStart(2, "0")}
    </div>
  );
}
