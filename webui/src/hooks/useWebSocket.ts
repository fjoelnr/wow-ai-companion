import { useCallback, useEffect, useRef, useState } from "react";
import type { ConnectionStatus, WSMessage } from "../utils/types";

const RECONNECT_DELAY = 3000;
const PING_INTERVAL = 30000;

interface UseWebSocketOptions {
  /** WebSocket path, e.g. "/ws/dashboard" */
  path: string;
  /** Called for each incoming message */
  onMessage: (msg: WSMessage) => void;
}

/**
 * WebSocket hook with automatic reconnection and ping/pong keepalive.
 */
export function useWebSocket({ path, onMessage }: UseWebSocketOptions) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}${path}`;

    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      // Start ping keepalive
      pingTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("ping");
        }
      }, PING_INTERVAL);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessage;
        onMessageRef.current(msg);
      } catch {
        // ignore non-JSON messages
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      if (pingTimer.current) clearInterval(pingTimer.current);
      // Auto-reconnect
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [path]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (pingTimer.current) clearInterval(pingTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { status };
}
