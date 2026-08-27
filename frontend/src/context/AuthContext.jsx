import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";

const AuthContext = createContext(null);

const API = "/api";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [refreshToken, setRefreshToken] = useState(() =>
    localStorage.getItem("refreshToken")
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [bootstrapping, setBootstrapping] = useState(
    () => !!localStorage.getItem("token")
  );
  const refreshTimerRef = useRef(null);

  const clearAuth = useCallback(() => {
    setUser(null);
    setToken(null);
    setRefreshToken(null);
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
    localStorage.removeItem("playerId");
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }
  }, []);

  const setTokens = useCallback((accessToken, refreshTokenValue, userData) => {
    setToken(accessToken);
    setRefreshToken(refreshTokenValue);
    setUser(userData);
    localStorage.setItem("token", accessToken);
    localStorage.setItem("refreshToken", refreshTokenValue);
    localStorage.setItem("user", JSON.stringify(userData));
  }, []);

  const updateUser = useCallback((updates) => {
    setUser((prev) => {
      const next = { ...prev, ...updates };
      localStorage.setItem("user", JSON.stringify(next));
      return next;
    });
  }, []);

  const refresh = useCallback(async () => {
    const currentRefresh = localStorage.getItem("refreshToken");
    if (!currentRefresh) {
      clearAuth();
      return null;
    }
    try {
      const res = await fetch(`${API}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: currentRefresh }),
      });
      const data = await res.json();
      if (!res.ok) {
        clearAuth();
        return null;
      }
      setTokens(data.access_token, data.refresh_token, data.user);
      return data.access_token;
    } catch (e) {
      clearAuth();
      return null;
    }
  }, [clearAuth, setTokens]);

  // Validate any stored session on boot so stale tokens
  // clear themselves instead of causing WS "connection lost" loops.
  useEffect(() => {
    let cancelled = false;
    const validate = async () => {
      const stored = localStorage.getItem("token");
      if (!stored) {
        setBootstrapping(false);
        return;
      }
      try {
        const res = await fetch(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${stored}` },
        });
        if (res.status === 401) {
          await refresh();
        }
      } catch {
        // Network error: leave the session as-is rather than forcing logout.
      } finally {
        if (!cancelled) setBootstrapping(false);
      }
    };
    validate();
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  // Auto-refresh access token every 13 minutes
  useEffect(() => {
    if (!token || !refreshToken) {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
        refreshTimerRef.current = null;
      }
      return;
    }
    refreshTimerRef.current = setInterval(() => {
      refresh();
    }, 13 * 60 * 1000);
    return () => {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    };
  }, [token, refreshToken, refresh]);

  const apiRequest = useCallback(
    async (path, options = {}) => {
      const headers = {
        ...options.headers,
        Authorization: `Bearer ${token}`,
      };
      const res = await fetch(`${API}${path}`, { ...options, headers });
      if (res.status === 401) {
        const newToken = await refresh();
        if (newToken) {
          return fetch(`${API}${path}`, {
            ...options,
            headers: { ...options.headers, Authorization: `Bearer ${newToken}` },
          });
        }
      }
      return res;
    },
    [token, refresh]
  );

  const register = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Registration failed");
      }
      setTokens(data.access_token, data.refresh_token, data.user);
      return data;
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [setTokens]);

  const login = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Login failed");
      }
      setTokens(data.access_token, data.refresh_token, data.user);
      return data;
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [setTokens]);

  const logout = useCallback(async () => {
    const currentRefresh = localStorage.getItem("refreshToken");
    if (currentRefresh) {
      try {
        await fetch(`${API}/auth/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token || ""}`,
          },
          body: JSON.stringify({ refresh_token: currentRefresh }),
        });
      } catch {
        // ignore
      }
    }
    clearAuth();
  }, [token, clearAuth]);

  const logoutAll = useCallback(async () => {
    await apiRequest("/auth/logout-all", { method: "POST" });
    clearAuth();
  }, [apiRequest, clearAuth]);

  const changePassword = useCallback(
    async (currentPassword, newPassword) => {
      const res = await apiRequest("/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Password change failed");
      }
      setTokens(data.access_token, data.refresh_token, data.user);
      return data;
    },
    [apiRequest, setTokens]
  );

  const requestPasswordReset = useCallback(async (username) => {
    const res = await fetch(`${API}/auth/password-reset-request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Password reset failed");
    }
    return data;
  }, []);

  const confirmPasswordReset = useCallback(async (token, newPassword) => {
    const res = await fetch(`${API}/auth/password-reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, new_password: newPassword }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Password reset failed");
    }
    return data;
  }, []);

  const deleteAccount = useCallback(async (password) => {
    const res = await apiRequest("/auth/me", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "Account deletion failed");
    }
    clearAuth();
  }, [apiRequest, clearAuth]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        refreshToken,
        loading,
        error,
        bootstrapping,
        register,
        login,
        logout,
        logoutAll,
        refresh,
        changePassword,
        requestPasswordReset,
        confirmPasswordReset,
        deleteAccount,
        apiRequest,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
