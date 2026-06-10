import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { ApiError, approvePipeline, listProjects } from "../api/client";
import type { Project } from "../api/types";
import { usePipelineStatus } from "../hooks/usePipelineStatus";
import { toDisplayStatus } from "../lib/pipelineDisplay";

const STAGE_LABELS: Record<string, string> = {
  STORY: "Story",
  SCRIPT: "Script",
  STORYBOARD: "Storyboard",
};

/**
 * Human review gate (US-08 / US-10). Approve or reject the current stub stage
 * output; status updates come from `GET /pipeline/status` (DB per D-32).
 */
export function ReviewPage() {
  const [project, setProject] = useState<Project | null>(null);
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

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
          setActionError("Failed to load project.");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const { status: pipeline, refresh } = usePipelineStatus(project?.id ?? null);

  if (!project && !actionError) {
    return <p className="page__subtitle">Loading review…</p>;
  }

  if (!project) {
    return (
      <section className="page">
        <p className="page__error" role="alert">
          {actionError}
        </p>
      </section>
    );
  }

  const apiStatus = pipeline?.status ?? "IDLE";
  const displayStatus = toDisplayStatus(apiStatus);
  const stage = pipeline?.current_stage;

  if (displayStatus !== "REVIEW" || !stage) {
    return <Navigate to="/" replace />;
  }

  const reviewStage = stage;

  async function handleApprove() {
    setSubmitting(true);
    setActionError(null);
    try {
      await approvePipeline({
        project_id: project!.id,
        stage: reviewStage,
        decision: "GRANT",
      });
      setNote("");
      refresh();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Approval failed.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReject() {
    if (!note.trim()) {
      setActionError("A note is required to reject.");
      return;
    }
    setSubmitting(true);
    setActionError(null);
    try {
      await approvePipeline({
        project_id: project!.id,
        stage: reviewStage,
        decision: "REJECT",
        note: note.trim(),
      });
      refresh();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Rejection failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page">
      <header className="page__header">
        <h1 className="page__title">Review — {STAGE_LABELS[reviewStage] ?? reviewStage}</h1>
        <span className="badge badge--review">REVIEW</span>
      </header>

      <div className="card">
        <p className="review__lead">
          Stub stage output is ready for human review. Approve to advance the pipeline, or
          reject with a note (regenerate lands in Sprint 3).
        </p>
        <p className="review__meta">
          Run <code className="table__hash">{pipeline?.run_id}</code> · stage{" "}
          <strong>{reviewStage}</strong>
        </p>

        <label className="form-row form-row--stacked" htmlFor="reject-note">
          <span className="form-row__label">Reject note</span>
          <textarea
            id="reject-note"
            className="review__note"
            rows={3}
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Required if rejecting…"
          />
        </label>

        {actionError && (
          <p className="page__error" role="alert">
            {actionError}
          </p>
        )}

        <div className="card__actions">
          <button
            type="button"
            className="button button--primary"
            disabled={submitting}
            onClick={() => void handleApprove()}
          >
            Approve stage
          </button>
          <button
            type="button"
            className="button"
            disabled={submitting}
            onClick={() => void handleReject()}
          >
            Reject
          </button>
          <Link className="button" to="/">
            Back to dashboard
          </Link>
        </div>
      </div>
    </section>
  );
}
