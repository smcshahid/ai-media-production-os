import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, listPipelineRuns } from "../api/client";
import type { PipelineRunSummary } from "../api/types";
import { formatCreatedAt } from "../lib/historyDisplay";

interface PipelineRunHistoryProps {
  projectId: string;
  activeRunId?: string | null;
}

export function PipelineRunHistory({ projectId, activeRunId }: PipelineRunHistoryProps) {
  const [runs, setRuns] = useState<PipelineRunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listPipelineRuns(projectId);
      setRuns(response.runs);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load pipeline runs.");
      setRuns([]);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return <p className="card__hint">Loading run history…</p>;
  }

  if (error) {
    return (
      <p className="page__error" role="alert">
        {error}
      </p>
    );
  }

  if (runs.length === 0) {
    return <p className="card__hint">No pipeline runs recorded yet.</p>;
  }

  return (
    <div className="run-history">
      <div className="run-history__toolbar">
        <button type="button" className="button" onClick={() => void load()}>
          Refresh
        </button>
      </div>
      <div className="table-wrap">
        <table className="table run-history__table">
          <thead>
            <tr>
              <th scope="col">Run</th>
              <th scope="col">Status</th>
              <th scope="col">Stage</th>
              <th scope="col">Assets</th>
              <th scope="col">Started</th>
              <th scope="col">Updated</th>
              <th scope="col">Links</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => {
              const isActive = activeRunId === run.run_id;
              return (
                <tr key={run.run_id} className={isActive ? "run-history__row--active" : undefined}>
                  <td>
                    <code className="table__hash">{run.run_id.slice(0, 8)}…</code>
                    {isActive && <span className="badge badge--review">current</span>}
                  </td>
                  <td>{run.status}</td>
                  <td>{run.current_stage ?? "—"}</td>
                  <td>{run.asset_count}</td>
                  <td>{formatCreatedAt(run.created_at)}</td>
                  <td>{formatCreatedAt(run.updated_at)}</td>
                  <td className="run-history__links">
                    <Link to={`/audit?run=${run.run_id}`}>Audit</Link>
                    <Link to={`/history?run=${run.run_id}`}>Assets</Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
