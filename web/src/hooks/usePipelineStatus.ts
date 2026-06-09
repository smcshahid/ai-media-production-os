import { useEffect, useState } from "react";

import { getPipelineStatus } from "../api/client";
import type { PipelineStatus } from "../api/types";

interface UsePipelineStatusResult {
  status: PipelineStatus | null;
  error: string | null;
  loading: boolean;
}

/**
 * Polls `GET /pipeline/status` for a project. The MVP defers WebSockets, so the
 * dashboard refreshes on an interval (Repository Structure §4.6). Passing a null
 * project id keeps the hook idle until the project list resolves.
 */
export function usePipelineStatus(
  projectId: string | null,
  intervalMs = 5000,
): UsePipelineStatusResult {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(projectId !== null);

  useEffect(() => {
    if (!projectId) {
      return;
    }

    let active = true;

    async function poll() {
      try {
        const next = await getPipelineStatus(projectId as string);
        if (active) {
          setStatus(next);
          setError(null);
        }
      } catch {
        if (active) {
          setError("Failed to load pipeline status.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void poll();
    const timer = window.setInterval(() => void poll(), intervalMs);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [projectId, intervalMs]);

  return { status, error, loading };
}
