import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "./AuthContext";
import useWebSocket from "../hooks/useWebSocket";

const DuelContext = createContext(null);

export function DuelProvider({ children }) {
  const { matchId } = useParams();
  const { token } = useAuth();
  const [playerId, setPlayerId] = useState(() => localStorage.getItem("playerId"));
  const [matchState, setMatchState] = useState(null);
  const [roundData, setRoundData] = useState(null);
  const [players, setPlayers] = useState({});
  const [lastSubmission, setLastSubmission] = useState(null);
  const [roundOver, setRoundOver] = useState(null);
  const [matchOver, setMatchOver] = useState(null);
  const [timerS, setTimerS] = useState(0);
  const [chatMessages, setChatMessages] = useState([]);

  const wsUrl = matchId && token
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws/duel/${matchId}?token=${token}`
    : null;

  const { send, subscribe, status } = useWebSocket(wsUrl);

  useEffect(() => {
    setChatMessages([]);
  }, [matchId]);

  useEffect(() => {
    if (!subscribe) return;
    return subscribe((msg) => {
      switch (msg.type) {
        case "match_state":
          setMatchState(msg);
          setRoundData(msg.round);
          setPlayers(msg.players || {});
          setTimerS(msg.round?.time_limit_s || 0);
          if (!playerId && msg.players) {
            const pids = Object.keys(msg.players);
            if (pids.length === 1) setPlayerId(pids[0]);
          }
          break;
        case "duel_state":
          setPlayers(msg.players || {});
          setLastSubmission(msg.submission_result);
          break;
        case "round_start":
          setRoundData(msg.round);
          setPlayers(msg.players || {});
          setRoundOver(null);
          setLastSubmission(null);
          setTimerS(msg.round?.time_limit_s || 0);
          break;
        case "round_over":
          setRoundOver(msg);
          setPlayers(msg.players || {});
          break;
        case "match_over":
          setMatchOver(msg);
          setPlayers(msg.players || {});
          break;
        case "chat":
          setChatMessages((prev) => [...prev, msg]);
          break;
      }
    });
  }, [subscribe, playerId]);

  useEffect(() => {
    if (timerS <= 0) return;
    const iv = setInterval(() => {
      setTimerS((t) => (t > 0 ? t - 1 : 0));
    }, 1000);
    return () => clearInterval(iv);
  }, [timerS > 0, matchState?.status]);

  const submitCode = useCallback(
    (code, telemetry) => {
      send({ type: "submit", code, telemetry });
    },
    [send]
  );

  return (
    <DuelContext.Provider
      value={{
        matchId,
        playerId,
        setPlayerId,
        matchState,
        roundData,
        players,
        lastSubmission,
        roundOver,
        matchOver,
        timerS,
        submitCode,
        send,
        status,
        chatMessages,
      }}
    >
      {children}
    </DuelContext.Provider>
  );
}

export function useDuel() {
  return useContext(DuelContext);
}
