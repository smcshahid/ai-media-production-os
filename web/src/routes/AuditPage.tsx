import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { listProjects } from "../api/client";
import type { Project } from "../api/types";
import { AuditTrailViewer } from "../components/AuditTrailViewer";

/** Audit trail route (US-23b / D-64) — read-only append-only event log. */
export function AuditPage() {
  const [searchParams] = useSearchParams();
  const initialRunId = searchParams.get("run");
  const [project, setProject] = useState<Project | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setLoadError(null);

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
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="page">
      <header className="page__header">
        <h1 className="page__title">Audit</h1>
      </header>

      {loadError && (
        <p className="page__error" role="alert">
          {loadError}
        </p>
      )}

      <div className="card">
        <h2 className="card__title">Pipeline audit trail</h2>
        <p className="card__hint">
          Immutable event log for pipeline starts, stage transitions, agent completions, asset
          storage, approvals, and exports.
        </p>

        {loading && <p className="card__hint">Loading…</p>}

        {!loading && !project && !loadError && (
          <p className="dashboard__guidance" role="note">
            No project available. <Link to="/">Return to Dashboard</Link>
          </p>
        )}

        {project && (
          <AuditTrailViewer projectId={project.id} initialRunId={initialRunId} />
        )}
      </div>
    </section>
  );
}
