import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function FriendsScreen() {
  const { token, user } = useAuth();
  const [friends, setFriends] = useState([]);
  const [requests, setRequests] = useState([]);
  const [tab, setTab] = useState("friends");
  const [addUsername, setAddUsername] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const api = "/api";

  const loadFriends = useCallback(async () => {
    const res = await fetch(`${api}/social/friends`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setFriends(await res.json());
  }, [token]);

  const loadRequests = useCallback(async () => {
    const res = await fetch(`${api}/social/friends/requests`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setRequests(await res.json());
  }, [token]);

  useEffect(() => {
    loadFriends();
    loadRequests();
  }, [loadFriends, loadRequests]);

  const handleAddFriend = async () => {
    const res = await fetch(`${api}/auth/users/by-username/${addUsername}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const target = await res.json();
    await fetch(`${api}/social/friends/request/${target.id}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    setAddUsername("");
    setSearchResults([]);
  };

  const handleAccept = async (userId) => {
    await fetch(`${api}/social/friends/accept/${userId}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    loadRequests();
    loadFriends();
  };

  const handleDecline = async (userId) => {
    await fetch(`${api}/social/friends/decline/${userId}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    loadRequests();
  };

  const handleRemove = async (userId) => {
    await fetch(`${api}/social/friends/remove/${userId}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    loadFriends();
  };

  const searchUsers = async (q) => {
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    const res = await fetch(`${api}/auth/users/search/${q}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setSearchResults(await res.json());
  };

  return (
    <div className="friends-screen">
      <div className="friends-card">
        <div className="friends-tabs">
          <button
            className={`friends-tab ${tab === "friends" ? "active" : ""}`}
            onClick={() => setTab("friends")}
          >
            Friends ({friends.length})
          </button>
          <button
            className={`friends-tab ${tab === "requests" ? "active" : ""}`}
            onClick={() => setTab("requests")}
          >
            Requests ({requests.length})
          </button>
          <button
            className={`friends-tab ${tab === "add" ? "active" : ""}`}
            onClick={() => setTab("add")}
          >
            Add Friend
          </button>
        </div>

        {tab === "friends" && (
          <div className="friends-list">
            {friends.length === 0 ? (
              <p className="friends-empty">No friends yet</p>
            ) : (
              friends.map((f) => (
                <div key={f.user_id} className="friends-row">
                  <Link to={`/profile/${f.user_id}`} className="friends-avatar">
                    {f.username[0].toUpperCase()}
                  </Link>
                  <div className="friends-info">
                    <Link to={`/profile/${f.user_id}`} className="friends-name">
                      {f.username}
                    </Link>
                    <span className="friends-elo">{f.elo} ELO</span>
                  </div>
                  <span
                    className={`friends-status ${f.online ? "online" : "offline"}`}
                  >
                    {f.online ? f.status : "Offline"}
                  </span>
                  <button
                    className="friends-remove-btn"
                    onClick={() => handleRemove(f.user_id)}
                  >
                    Remove
                  </button>
                </div>
              ))
            )}
          </div>
        )}

        {tab === "requests" && (
          <div className="friends-list">
            {requests.length === 0 ? (
              <p className="friends-empty">No pending requests</p>
            ) : (
              requests.map((r) => (
                <div key={r.user_id} className="friends-row">
                  <div className="friends-avatar">
                    {r.username[0].toUpperCase()}
                  </div>
                  <div className="friends-info">
                    <span className="friends-name">{r.username}</span>
                    <span className="friends-elo">{r.elo} ELO</span>
                  </div>
                  <div className="friends-actions">
                    <button
                      className="friends-accept-btn"
                      onClick={() => handleAccept(r.user_id)}
                    >
                      Accept
                    </button>
                    <button
                      className="friends-decline-btn"
                      onClick={() => handleDecline(r.user_id)}
                    >
                      Decline
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {tab === "add" && (
          <div className="friends-add">
            <input
              className="friends-search-input"
              type="text"
              placeholder="Search by username..."
              value={addUsername}
              onChange={(e) => {
                setAddUsername(e.target.value);
                searchUsers(e.target.value);
              }}
            />
            <button className="friends-send-btn" onClick={handleAddFriend}>
              Send Request
            </button>
            {searchResults.length > 0 && (
              <div className="friends-search-results">
                {searchResults.map((u) => (
                  <div
                    key={u.id}
                    className="friends-search-row"
                    onClick={() => setAddUsername(u.username)}
                  >
                    <span>{u.username}</span>
                    <span className="friends-search-elo">{u.elo} ELO</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
