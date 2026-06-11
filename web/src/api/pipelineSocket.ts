/**
 * WebSocket client for pipeline status push (US-21 D-59).
 */

import { clearToken, getToken } from "./client";
import type { PipelineStatus } from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

export type PipelineConnectionMode = "connecting" | "live" | "polling";

export interface PipelineSocketHandlers {
  onStatus: (status: PipelineStatus) => void;
  onModeChange: (mode: PipelineConnectionMode) => void;
}

function wsUrl(): string {
  const base = API_BASE_URL.replace(/^http/i, "ws");
  return `${base}/ws/pipeline`;
}

function parseStatus(payload: unknown): PipelineStatus | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const p = payload as PipelineStatus;
  if (typeof p.project_id !== "string" || typeof p.status !== "string") {
    return null;
  }
  return p;
}

function isNewer(incoming: PipelineStatus, current: PipelineStatus | null): boolean {
  if (!current?.updated_at) {
    return true;
  }
  if (!incoming.updated_at) {
    return false;
  }
  return incoming.updated_at >= current.updated_at;
}

export interface PipelineSocketHandle {
  close: () => void;
}

const BACKOFF_MS = [1000, 2000, 4000, 8000, 16000, 30000];

export function connectPipelineSocket(
  projectId: string,
  handlers: PipelineSocketHandlers,
  getLatestStatus: () => PipelineStatus | null,
): PipelineSocketHandle {
  let active = true;
  let socket: WebSocket | null = null;
  let reconnectAttempt = 0;
  let reconnectTimer: number | undefined;

  function setMode(mode: PipelineConnectionMode) {
    handlers.onModeChange(mode);
  }

  function scheduleReconnect() {
    if (!active) {
      return;
    }
    setMode("polling");
    const delay = BACKOFF_MS[Math.min(reconnectAttempt, BACKOFF_MS.length - 1)]!;
    reconnectAttempt += 1;
    reconnectTimer = window.setTimeout(() => {
      openSocket();
    }, delay);
  }

  function openSocket() {
    if (!active) {
      return;
    }
    setMode("connecting");
    const token = getToken();
    if (!token) {
      setMode("polling");
      return;
    }

    try {
      socket = new WebSocket(wsUrl());
    } catch {
      scheduleReconnect();
      return;
    }

    socket.onopen = () => {
      socket?.send(JSON.stringify({ type: "auth", token }));
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(String(event.data)) as {
          type?: string;
          payload?: unknown;
        };
        if (message.type === "auth.ok") {
          socket?.send(JSON.stringify({ type: "subscribe", project_id: projectId }));
          return;
        }
        if (message.type === "subscribed") {
          reconnectAttempt = 0;
          setMode("live");
          return;
        }
        if (message.type === "pipeline.status") {
          const next = parseStatus(message.payload);
          if (next && isNewer(next, getLatestStatus())) {
            handlers.onStatus(next);
          }
          return;
        }
        if (message.type === "ping") {
          socket?.send(JSON.stringify({ type: "pong" }));
        }
      } catch {
        // Ignore malformed frames.
      }
    };

    socket.onerror = () => {
      scheduleReconnect();
    };

    socket.onclose = (event) => {
      if (event.code === 4401) {
        clearToken();
        window.location.assign("/login");
        return;
      }
      scheduleReconnect();
    };
  }

  openSocket();

  return {
    close: () => {
      active = false;
      if (reconnectTimer !== undefined) {
        window.clearTimeout(reconnectTimer);
      }
      if (socket && socket.readyState <= WebSocket.OPEN) {
        socket.close(1000);
      }
      socket = null;
    },
  };
}
