import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { listProjects } from "../api/client";
import type { Project } from "../api/types";
import { AssetHistoryViewer } from "../components/AssetHistoryViewer";

/** Asset history route (US-23 D-58) — read-only D-57 browser. */
export function HistoryPage() {
  const [searchParams] = useSearchParams();
  const pipelineRunId = searchParams.get("run");
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
        <h1 className="page__title">History</h1>
      </header>

      {loadError && (
        <p className="page__error" role="alert">
          {loadError}
        </p>
      )}

      <div className="card">
        <h2 className="card__title">Asset version history</h2>
        <p className="card__hint">
          Read-only view of all asset versions by stage. Select a row for inline preview, version
          navigation, and Story/Script diffs.
        </p>

        {loading && <p className="card__hint">Loading…</p>}

        {!loading && !project && !loadError && (
          <p className="dashboard__guidance" role="note">
            No project available. <Link to="/">Return to Dashboard</Link>
          </p>
        )}

        {project && (
          <AssetHistoryViewer projectId={project.id} pipelineRunId={pipelineRunId} />
        )}
      </div>
    </section>
  );
}
