import { useEffect, useRef, useCallback, useState } from "react";

const MAX_RETRIES = 5;
const BASE_DELAY = 1000;

export default function useWebSocket(url) {
  const wsRef = useRef(null);
  const listenersRef = useRef([]);
  const retriesRef = useRef(0);
  const [status, setStatus] = useState("connecting");

  useEffect(() => {
    if (!url) return;

    let cancelled = false;
    let timeout;

    function connect() {
      if (cancelled) return;

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        retriesRef.current = 0;
        setStatus("connected");
      };

      ws.onclose = () => {
        if (cancelled) return;
        setStatus("disconnected");

        if (retriesRef.current < MAX_RETRIES) {
          const delay = BASE_DELAY * Math.pow(2, retriesRef.current);
          retriesRef.current++;
          timeout = setTimeout(connect, Math.min(delay, 10000));
        }
      };

      ws.onerror = () => {
        if (!cancelled) setStatus("error");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          listenersRef.current.forEach((fn) => fn(data));
        } catch {}
      };
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(timeout);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [url]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const subscribe = useCallback((fn) => {
    listenersRef.current.push(fn);
    return () => {
      listenersRef.current = listenersRef.current.filter((l) => l !== fn);
    };
  }, []);

  return { send, subscribe, status };
}
