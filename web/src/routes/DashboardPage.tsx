import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, listAssets, startPipeline, listProjects } from "../api/client";
import type { AssetVersion, Project } from "../api/types";
import { IdeaCaptureForm } from "../components/IdeaCaptureForm";
import { Stepper } from "../components/Stepper";
import { usePipelineStatus } from "../hooks/usePipelineStatus";
import {
  badgeClassForStatus,
  canStartPipeline,
  toDisplayStatus,
} from "../lib/pipelineDisplay";

const IDLE_STAGES = ["IDEA", "STORY", "SCRIPT", "STORYBOARD"];

const STAGE_LABELS: Record<string, string> = {
  IDEA: "Idea",
  STORY: "Story",
  SCRIPT: "Script",
  STORYBOARD: "Storyboard",
};

function latestIdeaVersion(assets: AssetVersion[]): AssetVersion | null {
  const ideas = assets.filter((asset) => asset.stage === "IDEA");
  if (ideas.length === 0) {
    return null;
  }
  return ideas.reduce((latest, current) =>
    current.version > latest.version ? current : latest,
  );
}

/**
 * Dashboard (US-10 + US-11): idea capture, live pipeline status from DB (D-32),
 * start workflow, stage stepper, and review CTA when awaiting approval.
 */
export function DashboardPage() {
  const [project, setProject] = useState<Project | null>(null);
  const [projectError, setProjectError] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [ideaVersion, setIdeaVersion] = useState<AssetVersion | null>(null);

  const refreshIdea = useCallback(async (projectId: string) => {
    const assets = await listAssets(projectId);
    setIdeaVersion(latestIdeaVersion(assets));
  }, []);

  useEffect(() => {
    let active = true;
    listProjects()
      .then(async (projects) => {
        const first = projects[0] ?? null;
        if (!active) {
          return;
        }
        setProject(first);
        if (first) {
          await refreshIdea(first.id);
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
  }, [refreshIdea]);

  const { status: pipeline, error: statusError, loading, refresh } = usePipelineStatus(
    project?.id ?? null,
  );

  const stages = pipeline?.stages ?? IDLE_STAGES;
  const apiStatus = pipeline?.status ?? "IDLE";
  const displayStatus = toDisplayStatus(apiStatus);
  const currentStage = pipeline?.current_stage ?? null;
  const hasIdea = ideaVersion !== null;

  async function handleStart() {
    if (!project) {
      return;
    }
    setStarting(true);
    setStartError(null);
    try {
      await startPipeline(project.id);
      refresh();
    } catch (err) {
      setStartError(err instanceof ApiError ? err.message : "Failed to start pipeline.");
    } finally {
      setStarting(false);
    }
  }

  const statusLine = (() => {
    if (loading && !pipeline) {
      return "Loading pipeline status…";
    }
    if (displayStatus === "IDLE") {
      return "No pipeline run yet.";
    }
    if (displayStatus === "GENERATING" && currentStage) {
      return `Generating ${STAGE_LABELS[currentStage] ?? currentStage} (stub activity)…`;
    }
    if (displayStatus === "REVIEW" && currentStage) {
      return `${STAGE_LABELS[currentStage] ?? currentStage} ready for your review.`;
    }
    if (displayStatus === "COMPLETED") {
      return "Pipeline completed — all stages approved.";
    }
    return `Status: ${displayStatus}`;
  })();

  return (
    <section className="page">
      <header className="page__header">
        <h1 className="page__title">{project?.name ?? "AIMPOS Spark Demo"}</h1>
        <span className={`badge ${badgeClassForStatus(displayStatus)}`}>{displayStatus}</span>
      </header>

      {projectError && (
        <p className="page__error" role="alert">
          {projectError}
        </p>
      )}
      {statusError && (
        <p className="page__error" role="alert">
          {statusError}
        </p>
      )}

      <div className="card">
        <h2 className="card__title">Idea</h2>
        {hasIdea && (
          <p className="dashboard__status-line">
            Idea saved — version {ideaVersion.version} (stage IDEA).{" "}
            <Link to="/assets">View in Assets</Link>
          </p>
        )}
        {project ? (
          <IdeaCaptureForm
            projectId={project.id}
            onSaved={() => void refreshIdea(project.id)}
          />
        ) : (
          <p className="card__hint">Loading project…</p>
        )}
      </div>

      <div className="card">
        <h2 className="card__title">Pipeline</h2>
        <p className="dashboard__status-line">{statusLine}</p>
        {!hasIdea && (
          <p className="dashboard__guidance" role="note">
            Save your idea above before starting the pipeline.
          </p>
        )}
        <Stepper stages={stages} currentStage={currentStage} status={apiStatus} />
        <div className="card__actions">
          {canStartPipeline(apiStatus) ? (
            <button
              type="button"
              className="button button--primary"
              disabled={starting || !project}
              onClick={() => void handleStart()}
            >
              {starting ? "Starting…" : "Start Pipeline"}
            </button>
          ) : (
            <button type="button" className="button button--primary" disabled>
              Pipeline active
            </button>
          )}

          {displayStatus === "REVIEW" && (
            <Link className="button button--primary" to="/review">
              Go to Review
            </Link>
          )}

          {displayStatus === "COMPLETED" && (
            <>
              <Link className="button button--primary" to="/export">
                Export bundle
              </Link>
              <span className="card__hint dashboard__completed">All stages approved</span>
            </>
          )}

          {startError && (
            <span className="page__error" role="alert">
              {startError}
            </span>
          )}
        </div>
      </div>
    </section>
  );
}
