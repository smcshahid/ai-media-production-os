import { useCallback, useEffect, useRef, useState } from "react";

import { getPipelineStatus } from "../api/client";
import type { PipelineStatus } from "../api/types";
import { pipelinePollIntervalMs } from "../lib/pipelineDisplay";

interface UsePipelineStatusResult {
  status: PipelineStatus | null;
  error: string | null;
  loading: boolean;
  /** Trigger an immediate refresh (e.g. after start/approve). */
  refresh: () => void;
}

/**
 * Polls `GET /pipeline/status` (DB source of truth per D-32). Interval is 5s
 * while the run is active; slower when idle or completed (US-10).
 */
export function usePipelineStatus(projectId: string | null): UsePipelineStatusResult {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(projectId !== null);
  const [refreshToken, setRefreshToken] = useState(0);
  const statusRef = useRef<PipelineStatus | null>(null);

  const refresh = useCallback(() => {
    setRefreshToken((value) => value + 1);
  }, []);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

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
      const interval = pipelinePollIntervalMs(statusRef.current?.status ?? null);
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
  }, [projectId, refreshToken]);

  return { status, error, loading, refresh };
}
