import { useCallback, useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import {
  ApiError,
  approvePipeline,
  getAssetContent,
  listAssets,
  listProjects,
  regeneratePipeline,
  updateAssetText,
} from "../api/client";
import type { AssetVersion, Project } from "../api/types";
import { usePipelineStatus } from "../hooks/usePipelineStatus";
import { toDisplayStatus } from "../lib/pipelineDisplay";
import { selectLatestAiDraftStoryAsset, selectLatestStoryAsset } from "../lib/storyReview";

const STAGE_LABELS: Record<string, string> = {
  STORY: "Story",
  SCRIPT: "Script",
  STORYBOARD: "Storyboard",
};

/**
 * Human review gate (US-08 / US-10 / US-13). STORY stage loads editable treatment;
 * approve/reject/regenerate via pipeline API (US-09 STORY regenerate).
 */
export function ReviewPage() {
  const [project, setProject] = useState<Project | null>(null);
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [rejectedHint, setRejectedHint] = useState(false);

  const [storyAsset, setStoryAsset] = useState<AssetVersion | null>(null);
  const [treatmentText, setTreatmentText] = useState("");
  const [savedText, setSavedText] = useState("");
  const [storyLoading, setStoryLoading] = useState(false);
  const [saving, setSaving] = useState(false);

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

  const { status: pipeline, refresh, error: pipelineError } = usePipelineStatus(
    project?.id ?? null,
  );

  const loadStory = useCallback(async (projectId: string, opts?: { preferAiDraft?: boolean }) => {
    setStoryLoading(true);
    setActionError(null);
    try {
      const assets = await listAssets(projectId);
      const latest = opts?.preferAiDraft
        ? selectLatestAiDraftStoryAsset(assets)
        : selectLatestStoryAsset(assets);
      if (!latest) {
        setStoryAsset(null);
        setTreatmentText("");
        setSavedText("");
        return;
      }
      const content = await getAssetContent(latest.id);
      setStoryAsset(latest);
      setTreatmentText(content);
      setSavedText(content);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to load story.");
    } finally {
      setStoryLoading(false);
    }
  }, []);

  const reviewStage = pipeline?.current_stage;
  const isStoryReview = reviewStage === "STORY";

  useEffect(() => {
    if (!project || !isStoryReview || pipeline?.status !== "AWAITING_APPROVAL") {
      return;
    }
    void loadStory(project.id);
  }, [project, isStoryReview, pipeline?.status, loadStory]);

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

  if (!pipeline) {
    if (pipelineError) {
      return (
        <section className="page">
          <p className="page__error" role="alert">
            {pipelineError}
          </p>
        </section>
      );
    }
    return <p className="page__subtitle">Loading review…</p>;
  }

  const apiStatus = pipeline.status;
  const displayStatus = toDisplayStatus(apiStatus);
  const stage = pipeline?.current_stage;

  if (displayStatus !== "REVIEW" || !stage) {
    return <Navigate to="/" replace />;
  }

  const dirty = isStoryReview && treatmentText !== savedText;

  async function handleSave() {
    if (!storyAsset || !dirty) {
      return;
    }
    setSaving(true);
    setActionError(null);
    try {
      const updated = await updateAssetText(storyAsset.id, treatmentText);
      setStoryAsset(updated);
      setSavedText(treatmentText);
      if (project) {
        await loadStory(project.id);
      }
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  async function handleApprove() {
    setSubmitting(true);
    setActionError(null);
    try {
      await approvePipeline({
        project_id: project!.id,
        stage: stage!,
        decision: "GRANT",
      });
      setNote("");
      setRejectedHint(false);
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
        stage: stage!,
        decision: "REJECT",
        note: note.trim(),
      });
      setRejectedHint(true);
      refresh();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Rejection failed.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRegenerate() {
    if (!project || !stage) {
      return;
    }
    setSubmitting(true);
    setActionError(null);
    try {
      await regeneratePipeline({ project_id: project.id, stage });
      refresh();
      await loadStory(project.id, { preferAiDraft: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setActionError(err.message);
      } else {
        setActionError(err instanceof ApiError ? err.message : "Regeneration failed.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page">
      <header className="page__header">
        <h1 className="page__title">Review — {STAGE_LABELS[stage] ?? stage}</h1>
        <span className="badge badge--review">REVIEW</span>
      </header>

      <div className="card">
        {isStoryReview ? (
          <>
            <p className="review__lead">
              Read and edit the generated story treatment. Save your changes, then approve to
              advance to script generation, or reject with a note.
            </p>
            {storyAsset && (
              <p className="review__meta">
                Version <strong>{storyAsset.version}</strong> · branch{" "}
                <code className="table__hash">{storyAsset.branch}</code>
                {storyAsset.is_ai_generated ? (
                  <span className="badge badge--generating" style={{ marginLeft: 8 }}>
                    AI Generated
                  </span>
                ) : null}
              </p>
            )}
            {storyLoading ? (
              <p className="page__subtitle">Loading treatment…</p>
            ) : storyAsset ? (
              <label className="form-row form-row--stacked" htmlFor="story-treatment">
                <span className="form-row__label">Story treatment</span>
                <textarea
                  id="story-treatment"
                  className="review__note review__treatment"
                  rows={16}
                  value={treatmentText}
                  onChange={(event) => setTreatmentText(event.target.value)}
                />
              </label>
            ) : (
              <p className="page__error" role="alert">
                No STORY asset found for this project.
              </p>
            )}
          </>
        ) : (
          <p className="review__lead">
            Stage output is ready for human review. Approve to advance the pipeline, or reject
            with a note.
          </p>
        )}

        <p className="review__meta">
          Run <code className="table__hash">{pipeline?.run_id}</code> · stage{" "}
          <strong>{stage}</strong>
        </p>

        {rejectedHint && isStoryReview && (
          <p className="review__regenerate-hint" role="status">
            Story rejected. Regenerate to request a new AI draft using your note, edit and save,
            or approve when ready. Up to 3 regenerations per run.
          </p>
        )}

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
          {isStoryReview && storyAsset && (
            <button
              type="button"
              className="button"
              disabled={saving || !dirty}
              onClick={() => void handleSave()}
            >
              {saving ? "Saving…" : "Save edits"}
            </button>
          )}
          <button
            type="button"
            className="button button--primary"
            disabled={submitting || (isStoryReview && dirty)}
            title={dirty ? "Save edits before approving" : undefined}
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
          {isStoryReview && (
            <button
              type="button"
              className="button"
              disabled={submitting || !rejectedHint || apiStatus === "RUNNING"}
              title={!rejectedHint ? "Reject with a note first" : undefined}
              onClick={() => void handleRegenerate()}
            >
              Regenerate
            </button>
          )}
          <Link className="button" to="/">
            Back to dashboard
          </Link>
        </div>
      </div>
    </section>
  );
}
