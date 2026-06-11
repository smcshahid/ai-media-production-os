import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listProjects } from "../api/client";
import type { Project } from "../api/types";
import { LineageViewer } from "../components/LineageViewer";
import { usePipelineStatus } from "../hooks/usePipelineStatus";
import { badgeClassForStatus, toDisplayStatus } from "../lib/pipelineDisplay";

/** Dedicated lineage route (US-20 D-56) — same viewer as Export page. */
export function LineagePage() {
  const [project, setProject] = useState<Project | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

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

  return (
    <section className="page">
      <header className="page__header">
        <h1 className="page__title">Lineage</h1>
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
        <h2 className="card__title">Asset provenance</h2>
        <p className="card__hint">
          Read-only view of how approved assets connect from idea through video.
        </p>

        {loading && !pipeline && <p className="card__hint">Loading pipeline status…</p>}

        {!loading && !isCompleted && (
          <p className="dashboard__guidance" role="note">
            Lineage is available only when the pipeline is <strong>COMPLETED</strong>.{" "}
            <Link to="/">Return to Dashboard</Link>
          </p>
        )}

        {isCompleted && runId && <LineageViewer runId={runId} />}
      </div>
    </section>
  );
}
