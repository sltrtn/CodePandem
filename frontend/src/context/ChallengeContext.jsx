import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useCallback,
} from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { useToast } from "../components/Toast";

const ChallengeContext = createContext(null);

export function ChallengeProvider({ children }) {
  const { token, user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [pending, setPending] = useState([]);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!token) return;

    const ws = new WebSocket(`${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws/challenge?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      toast("Challenge notifications connected", "info", 2000);
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch (msg.type) {
        case "challenge_received":
          setPending((prev) => [
            ...prev,
            {
              challengeId: msg.challenge_id,
              challengerId: msg.challenger_id,
              challengerUsername: msg.challenger_username,
            },
          ]);
          toast(`${msg.challenger_username} challenged you!`, "info", 5000);
          break;
        case "challenge_accepted":
          toast("Challenge accepted! Starting match...", "success", 2000);
          if (msg.match_id) {
            navigate(`/duel/${msg.match_id}`);
          }
          break;
        case "challenge_declined":
          toast("Challenge declined", "error", 2000);
          break;
        case "challenge_sent":
          toast("Challenge sent!", "info", 2000);
          break;
        case "error":
          toast(msg.message || "Challenge error", "error", 3000);
          break;
      }
    };

    return () => ws.close();
  }, [token, toast, navigate]);

  const sendChallenge = useCallback((targetId) => {
    wsRef.current?.send(
      JSON.stringify({ type: "challenge_player", target_id: targetId })
    );
  }, []);

  const acceptChallenge = useCallback((challengeId) => {
    wsRef.current?.send(
      JSON.stringify({ type: "accept_challenge", challenge_id: challengeId })
    );
    setPending((prev) => prev.filter((p) => p.challengeId !== challengeId));
  }, []);

  const declineChallenge = useCallback((challengeId) => {
    wsRef.current?.send(
      JSON.stringify({ type: "decline_challenge", challenge_id: challengeId })
    );
    setPending((prev) => prev.filter((p) => p.challengeId !== challengeId));
  }, []);

  return (
    <ChallengeContext.Provider
      value={{
        pending,
        sendChallenge,
        acceptChallenge,
        declineChallenge,
      }}
    >
      {children}
      {pending.length > 0 && (
        <div className="challenge-overlay">
          <div className="challenge-dialog">
            <h3>Incoming Challenge</h3>
            {pending.map((c) => (
              <div key={c.challengeId} className="challenge-item">
                <div className="challenge-avatar">
                  {c.challengerUsername[0].toUpperCase()}
                </div>
                <div className="challenge-info">
                  <div className="challenge-name">{c.challengerUsername}</div>
                  <div className="challenge-sub">wants to duel</div>
                </div>
                <div className="challenge-actions">
                  <button
                    className="challenge-accept-btn"
                    onClick={() => acceptChallenge(c.challengeId)}
                  >
                    Accept
                  </button>
                  <button
                    className="challenge-decline-btn"
                    onClick={() => declineChallenge(c.challengeId)}
                  >
                    Decline
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </ChallengeContext.Provider>
  );
}

export function useChallenge() {
  return useContext(ChallengeContext);
}
