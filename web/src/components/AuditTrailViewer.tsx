import { useCallback, useEffect, useMemo, useState } from "react";

import {
  ApiError,
  downloadAuditExport,
  getAuditTrail,
  getPipelineStatus,
  listPipelineRuns,
} from "../api/client";
import type { AuditEventRow } from "../api/types";

const PAGE_SIZE = 100;

interface AuditTrailViewerProps {
  projectId: string;
  initialRunId?: string | null;
}

function formatPayload(payload: Record<string, unknown> | null): string {
  if (!payload || Object.keys(payload).length === 0) {
    return "—";
  }
  const parts = Object.entries(payload)
    .slice(0, 4)
    .map(([key, value]) => `${key}=${String(value)}`);
  return parts.join(" · ");
}

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString();
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function AuditTrailViewer({ projectId, initialRunId }: AuditTrailViewerProps) {
  const [events, setEvents] = useState<AuditEventRow[]>([]);
  const [runFilter, setRunFilter] = useState<string>(initialRunId ?? "");
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runOptions, setRunOptions] = useState<string[]>([]);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<"csv" | "json" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const effectiveFilter = runFilter || activeRunId || undefined;

  const loadRuns = useCallback(async () => {
    try {
      const runs = await listPipelineRuns(projectId);
      setRunOptions(runs.runs.map((run) => run.run_id));
    } catch {
      // Run list is optional for the audit viewer.
    }
  }, [projectId]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const status = await getPipelineStatus(projectId);
      const latestRun = status.run_id;
      setActiveRunId(latestRun);
      const filter = runFilter || latestRun;
      const trail = await getAuditTrail(projectId, filter ?? undefined, {
        limit: PAGE_SIZE,
        offset,
      });
      setEvents(trail.events);
      setTotal(trail.total);
      setHasMore(trail.has_more);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load audit trail.");
      setEvents([]);
      setTotal(0);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [projectId, runFilter, offset]);

  useEffect(() => {
    void loadRuns();
  }, [loadRuns]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (initialRunId) {
      setRunFilter(initialRunId);
    }
  }, [initialRunId]);

  useEffect(() => {
    setOffset(0);
  }, [runFilter, initialRunId]);

  const pageStart = total === 0 ? 0 : offset + 1;
  const pageEnd = offset + events.length;
  const canPrev = offset > 0;
  const canNext = hasMore;

  const selectOptions = useMemo(() => {
    const ids = new Set(runOptions);
    if (activeRunId) {
      ids.add(activeRunId);
    }
    if (initialRunId) {
      ids.add(initialRunId);
    }
    return Array.from(ids);
  }, [runOptions, activeRunId, initialRunId]);

  async function handleExport(format: "csv" | "json") {
    setExporting(format);
    setError(null);
    try {
      const filter = runFilter || activeRunId;
      const blob = await downloadAuditExport(projectId, format, filter ?? undefined);
      const scope = filter ? filter.slice(0, 8) : "all";
      triggerDownload(blob, `audit-${scope}.${format}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Export failed.");
    } finally {
      setExporting(null);
    }
  }

  return (
    <div className="audit-trail">
      <div className="audit-trail__toolbar">
        <label className="audit-trail__filter">
          Pipeline run
          <select
            value={runFilter}
            onChange={(event) => setRunFilter(event.target.value)}
            aria-label="Filter audit events by pipeline run"
          >
            <option value="">Latest run</option>
            {selectOptions.map((runId) => (
              <option key={runId} value={runId}>
                {runId.slice(0, 8)}…
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="button" onClick={() => void load()} disabled={loading}>
          Refresh
        </button>
        <button
          type="button"
          className="button"
          disabled={loading || exporting !== null}
          onClick={() => void handleExport("csv")}
        >
          {exporting === "csv" ? "Exporting…" : "Export CSV"}
        </button>
        <button
          type="button"
          className="button"
          disabled={loading || exporting !== null}
          onClick={() => void handleExport("json")}
        >
          {exporting === "json" ? "Exporting…" : "Export JSON"}
        </button>
      </div>

      {error && (
        <p className="page__error" role="alert">
          {error}
        </p>
      )}

      {loading && <p className="card__hint">Loading audit events…</p>}

      {!loading && !error && events.length === 0 && (
        <p className="card__hint">No audit events recorded for this project yet.</p>
      )}

      {!loading && events.length > 0 && (
        <>
          <p className="audit-trail__page-info">
            Showing {pageStart}–{pageEnd} of {total}
            {effectiveFilter ? ` · run ${effectiveFilter.slice(0, 8)}…` : ""}
          </p>
          <div className="table-wrap">
            <table className="table audit-trail__table">
              <thead>
                <tr>
                  <th scope="col">Time</th>
                  <th scope="col">Event</th>
                  <th scope="col">Run</th>
                  <th scope="col">Details</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td>{formatTimestamp(event.created_at)}</td>
                    <td>
                      <code>{event.event_type}</code>
                    </td>
                    <td>
                      {event.pipeline_run_id ? (
                        <code className="table__hash">{event.pipeline_run_id.slice(0, 8)}…</code>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>{formatPayload(event.payload)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="audit-trail__pager">
            <button
              type="button"
              className="button"
              disabled={loading || !canPrev}
              onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
            >
              Previous
            </button>
            <button
              type="button"
              className="button"
              disabled={loading || !canNext}
              onClick={() => setOffset((value) => value + PAGE_SIZE)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
