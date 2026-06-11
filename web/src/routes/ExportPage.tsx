import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, downloadExport, listProjects } from "../api/client";
import type { Project } from "../api/types";
import { usePipelineStatus } from "../hooks/usePipelineStatus";
import { badgeClassForStatus, toDisplayStatus } from "../lib/pipelineDisplay";

/**
 * Export page (US-19): download production bundle when pipeline is COMPLETED.
 */
export function ExportPage() {
  const [project, setProject] = useState<Project | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    let active = true;
    listProjects()
      .then((projects) => {
        if (active) {
          setProject(projects[0] ?? null);
        }
      })
      .catch(() => {
        if (active) {
          setLoadError("Failed to load project.");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const { status: pipeline, error: statusError, loading } = usePipelineStatus(
    project?.id ?? null,
  );

  const apiStatus = pipeline?.status ?? "IDLE";
  const displayStatus = toDisplayStatus(apiStatus);
  const isCompleted = apiStatus === "COMPLETED";
  const runId = pipeline?.run_id ?? null;

  const handleDownload = useCallback(async () => {
    if (!runId) {
      return;
    }
    setExporting(true);
    setExportError(null);
    try {
      const blob = await downloadExport(runId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `aimpos-export-${runId}.zip`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setExportError(err instanceof ApiError ? err.message : "Export failed.");
    } finally {
      setExporting(false);
    }
  }, [runId]);

  return (
    <section className="page">
      <header className="page__header">
        <h1 className="page__title">Export</h1>
        <span className={`badge ${badgeClassForStatus(displayStatus)}`}>{displayStatus}</span>
      </header>

      {loadError && (
        <p className="page__error" role="alert">
          {loadError}
        </p>
      )}
      {statusError && (
        <p className="page__error" role="alert">
          {statusError}
        </p>
      )}

      <div className="card">
        <h2 className="card__title">Production bundle</h2>
        <p className="card__hint">
          Download a ZIP of all approved assets (idea through video) with a verifiable
          manifest.json.
        </p>

        {loading && !pipeline && <p className="card__hint">Loading pipeline status…</p>}

        {!loading && !isCompleted && (
          <p className="dashboard__guidance" role="note">
            Export is available only when the pipeline is <strong>COMPLETED</strong>.{" "}
            <Link to="/">Return to Dashboard</Link>
          </p>
        )}

        {isCompleted && runId && (
          <div className="card__actions">
            <button
              type="button"
              className="button button--primary"
              disabled={exporting}
              onClick={() => void handleDownload()}
            >
              {exporting ? "Preparing…" : "Download bundle"}
            </button>
            <p className="card__hint">Run {runId}</p>
          </div>
        )}

        {exportError && (
          <p className="page__error" role="alert">
            {exportError}
          </p>
        )}
      </div>
    </section>
  );
}
