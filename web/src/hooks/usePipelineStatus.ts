import { useCallback, useEffect, useRef, useState } from "react";

import { getPipelineStatus } from "../api/client";
import {
  connectPipelineSocket,
  type PipelineConnectionMode,
} from "../api/pipelineSocket";
import type { PipelineStatus } from "../api/types";
import { pipelineLivePollIntervalMs, pipelinePollIntervalMs } from "../lib/pipelineDisplay";

interface UsePipelineStatusResult {
  status: PipelineStatus | null;
  error: string | null;
  loading: boolean;
  connectionMode: PipelineConnectionMode;
  /** Trigger an immediate refresh (e.g. after start/approve). */
  refresh: () => void;
}

/**
 * Pipeline status from REST (authoritative) with optional WebSocket push (US-21 D-59).
 * Polling fallback always active — faster when not live.
 */
export function usePipelineStatus(projectId: string | null): UsePipelineStatusResult {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(projectId !== null);
  const [connectionMode, setConnectionMode] = useState<PipelineConnectionMode>("polling");
  const [refreshToken, setRefreshToken] = useState(0);
  const statusRef = useRef<PipelineStatus | null>(null);
  const connectionModeRef = useRef<PipelineConnectionMode>("polling");

  const refresh = useCallback(() => {
    setRefreshToken((value) => value + 1);
  }, []);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    connectionModeRef.current = connectionMode;
  }, [connectionMode]);

  useEffect(() => {
    if (!projectId) {
      return;
    }

    let active = true;
    let timer: number | undefined;

    async function poll() {
      try {
        const next = await getPipelineStatus(projectId as string);
        if (active) {
          setStatus(next);
          setError(null);
        }
        return next;
      } catch {
        if (active) {
          setError("Failed to load pipeline status.");
        }
        return null;
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    function scheduleNext() {
      const interval =
        connectionModeRef.current === "live"
          ? pipelineLivePollIntervalMs()
          : pipelinePollIntervalMs(statusRef.current?.status ?? null);
      timer = window.setTimeout(async () => {
        await poll();
        if (active) {
          scheduleNext();
        }
      }, interval);
    }

    void poll().then(() => {
      if (active) {
        scheduleNext();
      }
    });

    return () => {
      active = false;
      if (timer !== undefined) {
        window.clearTimeout(timer);
      }
    };
  }, [projectId, refreshToken, connectionMode]);

  useEffect(() => {
    if (!projectId) {
      setConnectionMode("polling");
      return;
    }

    const handle = connectPipelineSocket(
      projectId,
      {
        onStatus: (next) => {
          setStatus(next);
          setError(null);
          setLoading(false);
        },
        onModeChange: (mode) => {
          setConnectionMode(mode);
        },
      },
      () => statusRef.current,
    );

    return () => {
      handle.close();
      setConnectionMode("polling");
    };
  }, [projectId]);

  return { status, error, loading, connectionMode, refresh };
}
