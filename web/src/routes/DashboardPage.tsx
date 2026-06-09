import { useEffect, useState } from "react";

import { listProjects } from "../api/client";
import type { Project } from "../api/types";
import { Stepper } from "../components/Stepper";
import { usePipelineStatus } from "../hooks/usePipelineStatus";

const IDLE_STAGES = ["IDEA", "STORY", "SCRIPT", "STORYBOARD"];

/**
 * Dashboard (US-10): shows the demo project name and the 4-stage stepper in its
 * idle state. "Start Pipeline" is intentionally disabled — pipeline execution
 * arrives in Sprint 1.
 */
export function DashboardPage() {
  const [project, setProject] = useState<Project | null>(null);
  const [projectError, setProjectError] = useState<string | null>(null);

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
          setProjectError("Failed to load the project.");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const { status: pipeline } = usePipelineStatus(project?.id ?? null);

  const stages = pipeline?.stages ?? IDLE_STAGES;
  const status = pipeline?.status ?? "IDLE";
  const currentStage = pipeline?.current_stage ?? null;

  return (
    <section className="page">
      <header className="page__header">
        <h1 className="page__title">{project?.name ?? "AIMPOS Spark Demo"}</h1>
        <span className={`badge badge--${status === "IDLE" ? "idle" : "active"}`}>{status}</span>
      </header>

      {projectError && (
        <p className="page__error" role="alert">
          {projectError}
        </p>
      )}

      <div className="card">
        <h2 className="card__title">Pipeline</h2>
        <Stepper stages={stages} currentStage={currentStage} status={status} />
        <div className="card__actions">
          <button
            type="button"
            className="button button--primary"
            disabled
            title="Coming in Sprint 1"
          >
            Start Pipeline
          </button>
          <span className="card__hint">Coming in Sprint 1</span>
        </div>
      </div>
    </section>
  );
}
