import { useState, useEffect, useRef } from "react";
import { useDuel } from "../context/DuelContext";

export default function ChatPanel() {
  const { sendMessage, playerId, chatMessages } = useDuel();
  const [text, setText] = useState("");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const handleSend = () => {
    if (!text.trim()) return;
    sendMessage({ type: "chat", text: text.trim() });
    setText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      <h4 className="chat-title">Match Chat</h4>
      <div className="chat-messages">
        {(chatMessages || []).map((msg, i) => (
          <div
            key={i}
            className={`chat-message ${
              msg.player_id === playerId ? "me" : ""
            }`}
          >
            <span className="chat-username">{msg.username}</span>
            <span className="chat-text">{msg.text}</span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-row">
        <input
          className="chat-input"
          type="text"
          placeholder="Type a message..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={500}
        />
        <button className="chat-send-btn" onClick={handleSend} disabled={!text.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
