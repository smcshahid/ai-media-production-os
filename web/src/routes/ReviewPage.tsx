import { useCallback, useEffect, useRef, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import {
  ApiError,
  approvePipeline,
  getAssetContent,
  getAssetContentBlob,
  listAssets,
  listProjects,
  regeneratePipeline,
  updateAssetText,
} from "../api/client";
import type { AssetVersion, Project } from "../api/types";
import { StoryboardLightbox } from "../components/StoryboardLightbox";
import { usePipelineStatus } from "../hooks/usePipelineStatus";
import { formatFountainHtml } from "../lib/fountainFormat";
import { toDisplayStatus } from "../lib/pipelineDisplay";
import { selectLatestAiDraftScriptAsset } from "../lib/scriptReview";
import { batchVersion, selectLatestStoryboardBatch } from "../lib/storyboardReview";
import { selectLatestAiDraftStoryAsset, selectLatestStoryAsset } from "../lib/storyReview";
import { selectLatestAiDraftVideoAsset, videoSourceLabel } from "../lib/videoReview";
import { formatReviewActionError } from "../lib/reviewErrors";

const STAGE_LABELS: Record<string, string> = {
  STORY: "Story",
  SCRIPT: "Script",
  STORYBOARD: "Storyboard",
  VIDEO: "Video",
};

/**
 * Human review gate (US-08 / US-10 / US-13 / US-15 / US-17). STORY: editable treatment.
 * SCRIPT: Fountain preview. STORYBOARD: PNG gallery. Approve/reject/regenerate via pipeline API.
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

  const [scriptAsset, setScriptAsset] = useState<AssetVersion | null>(null);
  const [scriptPreviewHtml, setScriptPreviewHtml] = useState("");
  const [scriptLoading, setScriptLoading] = useState(false);

  const [storyboardFrames, setStoryboardFrames] = useState<AssetVersion[]>([]);
  const [storyboardImageUrls, setStoryboardImageUrls] = useState<Record<string, string>>({});
  const [storyboardLoading, setStoryboardLoading] = useState(false);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const storyboardImageUrlsRef = useRef<Record<string, string>>({});

  const [videoAsset, setVideoAsset] = useState<AssetVersion | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [videoLoading, setVideoLoading] = useState(false);
  const videoUrlRef = useRef<string | null>(null);

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

  const loadScript = useCallback(async (projectId: string) => {
    setScriptLoading(true);
    setActionError(null);
    try {
      const assets = await listAssets(projectId);
      const latest = selectLatestAiDraftScriptAsset(assets);
      if (!latest) {
        setScriptAsset(null);
        setScriptPreviewHtml("");
        return;
      }
      const content = await getAssetContent(latest.id);
      setScriptAsset(latest);
      setScriptPreviewHtml(formatFountainHtml(content));
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to load script.");
    } finally {
      setScriptLoading(false);
    }
  }, []);

  const revokeStoryboardUrls = useCallback((urls: Record<string, string>) => {
    Object.values(urls).forEach((url) => URL.revokeObjectURL(url));
  }, []);

  const loadStoryboard = useCallback(async (projectId: string) => {
    setStoryboardLoading(true);
    setActionError(null);
    try {
      const assets = await listAssets(projectId);
      const batch = selectLatestStoryboardBatch(assets);
      if (!batch) {
        setStoryboardFrames([]);
        setStoryboardImageUrls((prev) => {
          revokeStoryboardUrls(prev);
          return {};
        });
        return;
      }
      const urls: Record<string, string> = {};
      for (const frame of batch) {
        const blob = await getAssetContentBlob(frame.id, "image/png");
        urls[frame.id] = URL.createObjectURL(blob);
      }
      setStoryboardImageUrls((prev) => {
        revokeStoryboardUrls(prev);
        return urls;
      });
      storyboardImageUrlsRef.current = urls;
      setStoryboardFrames(batch);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to load storyboard.");
    } finally {
      setStoryboardLoading(false);
    }
  }, [revokeStoryboardUrls]);

  const revokeVideoUrl = useCallback((url: string | null) => {
    if (url) {
      URL.revokeObjectURL(url);
    }
  }, []);

  const loadVideo = useCallback(async (projectId: string) => {
    setVideoLoading(true);
    setActionError(null);
    try {
      const assets = await listAssets(projectId);
      const latest = selectLatestAiDraftVideoAsset(assets);
      if (!latest) {
        setVideoAsset(null);
        setVideoUrl((prev) => {
          revokeVideoUrl(prev);
          return null;
        });
        return;
      }
      const blob = await getAssetContentBlob(latest.id, "video/mp4");
      const url = URL.createObjectURL(blob);
      setVideoAsset(latest);
      setVideoUrl((prev) => {
        revokeVideoUrl(prev);
        return url;
      });
      videoUrlRef.current = url;
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to load video.");
    } finally {
      setVideoLoading(false);
    }
  }, [revokeVideoUrl]);

  useEffect(() => {
    videoUrlRef.current = videoUrl;
  }, [videoUrl]);

  useEffect(() => {
    return () => {
      revokeVideoUrl(videoUrlRef.current);
    };
  }, [revokeVideoUrl]);

  useEffect(() => {
    storyboardImageUrlsRef.current = storyboardImageUrls;
  }, [storyboardImageUrls]);

  useEffect(() => {
    return () => {
      revokeStoryboardUrls(storyboardImageUrlsRef.current);
    };
  }, [revokeStoryboardUrls]);

  const reviewStage = pipeline?.current_stage;
  const isStoryReview = reviewStage === "STORY";
  const isScriptReview = reviewStage === "SCRIPT";
  const isStoryboardReview = reviewStage === "STORYBOARD";
  const isVideoReview = reviewStage === "VIDEO";

  useEffect(() => {
    if (!project || !isStoryReview || pipeline?.status !== "AWAITING_APPROVAL") {
      return;
    }
    void loadStory(project.id);
  }, [project, isStoryReview, pipeline?.status, loadStory]);

  useEffect(() => {
    if (!project || !isScriptReview || pipeline?.status !== "AWAITING_APPROVAL") {
      return;
    }
    void loadScript(project.id);
  }, [project, isScriptReview, pipeline?.status, loadScript]);

  useEffect(() => {
    if (!project || !isStoryboardReview || pipeline?.status !== "AWAITING_APPROVAL") {
      return;
    }
    void loadStoryboard(project.id);
  }, [project, isStoryboardReview, pipeline?.status, loadStoryboard]);

  useEffect(() => {
    if (!project || !isVideoReview || pipeline?.status !== "AWAITING_APPROVAL") {
      return;
    }
    void loadVideo(project.id);
  }, [project, isVideoReview, pipeline?.status, loadVideo]);

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
  const canRegenerate =
    (isStoryReview || isScriptReview || isStoryboardReview || isVideoReview) &&
    rejectedHint &&
    apiStatus !== "RUNNING";

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
      setActionError(formatReviewActionError(err, "Approval failed."));
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
      setActionError(formatReviewActionError(err, "Rejection failed."));
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
      if (isStoryReview) {
        await loadStory(project.id, { preferAiDraft: true });
      } else if (isScriptReview) {
        await loadScript(project.id);
      } else if (isStoryboardReview) {
        await loadStoryboard(project.id);
      } else if (isVideoReview) {
        await loadVideo(project.id);
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setActionError(err.message);
      } else {
        setActionError(formatReviewActionError(err, "Regeneration failed."));
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
        ) : isScriptReview ? (
          <>
            <p className="review__lead">
              Preview the generated Fountain script. Approve to advance to storyboard generation,
              or reject with a note to regenerate.
            </p>
            {scriptAsset && (
              <p className="review__meta">
                Version <strong>{scriptAsset.version}</strong> · branch{" "}
                <code className="table__hash">{scriptAsset.branch}</code>
                {scriptAsset.is_ai_generated ? (
                  <span className="badge badge--generating" style={{ marginLeft: 8 }}>
                    AI Generated
                  </span>
                ) : null}
              </p>
            )}
            {scriptLoading ? (
              <p className="page__subtitle">Loading script…</p>
            ) : scriptAsset ? (
              <div
                className="fountain-preview"
                dangerouslySetInnerHTML={{ __html: scriptPreviewHtml }}
              />
            ) : (
              <p className="page__error" role="alert">
                No SCRIPT asset found for this project.
              </p>
            )}
          </>
        ) : isStoryboardReview ? (
          <>
            <p className="review__lead">
              Review all four storyboard frames as a batch. Approve to advance to video
              generation, or reject with a note to regenerate a new frame set.
            </p>
            {storyboardFrames.length > 0 && (
              <p className="review__meta">
                Batch version <strong>{batchVersion(storyboardFrames)}</strong> ·{" "}
                {storyboardFrames.length} frames · branch{" "}
                <code className="table__hash">{storyboardFrames[0]?.branch}</code>
              </p>
            )}
            {storyboardLoading ? (
              <p className="page__subtitle">Loading storyboard…</p>
            ) : storyboardFrames.length > 0 ? (
              <div className="storyboard-grid">
                {storyboardFrames.map((frame, idx) => {
                  const meta = frame.metadata_json ?? {};
                  const frameNum =
                    typeof meta.frame_index === "number"
                      ? meta.frame_index
                      : typeof meta.frame_index === "string"
                        ? meta.frame_index
                        : idx + 1;
                  const shotLabel =
                    typeof meta.shot_label === "string" ? meta.shot_label : null;
                  return (
                    <button
                      key={frame.id}
                      type="button"
                      className="storyboard-grid__tile"
                      onClick={() => setLightboxIndex(idx)}
                    >
                      {storyboardImageUrls[frame.id] ? (
                        <img
                          className="storyboard-grid__thumb"
                          src={storyboardImageUrls[frame.id]}
                          alt={`Storyboard frame ${frameNum}`}
                        />
                      ) : (
                        <span className="storyboard-grid__placeholder">No preview</span>
                      )}
                      <span className="storyboard-grid__caption">
                        Frame {frameNum}
                        {shotLabel ? ` · ${shotLabel}` : ""}
                      </span>
                      {frame.is_ai_generated ? (
                        <span className="badge badge--generating storyboard-grid__badge">
                          AI Generated
                        </span>
                      ) : null}
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="page__error" role="alert">
                Storyboard batch incomplete or missing. Expected 4 frames at the latest version.
              </p>
            )}
          </>
        ) : isVideoReview ? (
          <>
            <p className="review__lead">
              Preview the generated scene video. Approve to complete the pipeline, or reject with
              a note to regenerate.
            </p>
            {videoAsset && (
              <p className="review__meta">
                Version <strong>{videoAsset.version}</strong> ·{" "}
                {videoSourceLabel(videoAsset)} · branch{" "}
                <code className="table__hash">{videoAsset.branch}</code>
                {typeof videoAsset.metadata_json?.duration_sec === "number" ? (
                  <>
                    {" "}
                    · {videoAsset.metadata_json.duration_sec}s
                  </>
                ) : null}
              </p>
            )}
            {videoLoading ? (
              <p className="page__subtitle">Loading video…</p>
            ) : videoAsset && videoUrl ? (
              <video className="review__video" controls src={videoUrl}>
                Scene video preview
              </video>
            ) : (
              <p className="page__error" role="alert">
                No VIDEO asset found for this run. If generation is still running, wait and refresh.
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

        {rejectedHint && isScriptReview && (
          <p className="review__regenerate-hint" role="status">
            Script rejected. Regenerate to request a new AI draft using your note, or approve when
            ready. Up to 3 regenerations per run.
          </p>
        )}

        {rejectedHint && isStoryboardReview && (
          <p className="review__regenerate-hint" role="status">
            Storyboard batch rejected. Regenerate to request a new 4-frame set using your note, or
            approve all frames when ready. Up to 3 regenerations per run.
          </p>
        )}

        {rejectedHint && isVideoReview && (
          <p className="review__regenerate-hint" role="status">
            Video rejected. Regenerate to request a new MP4 using your note, or approve when ready.
            Up to 3 regenerations per run.
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
            Approve{isStoryboardReview ? " all frames" : " stage"}
          </button>
          <button
            type="button"
            className="button"
            disabled={submitting}
            onClick={() => void handleReject()}
          >
            Reject
          </button>
          {(isStoryReview || isScriptReview || isStoryboardReview || isVideoReview) && (
            <button
              type="button"
              className="button"
              disabled={submitting || !canRegenerate}
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

      {lightboxIndex !== null && storyboardFrames.length > 0 && (
        <StoryboardLightbox
          frames={storyboardFrames}
          imageUrls={storyboardImageUrls}
          index={lightboxIndex}
          onClose={() => setLightboxIndex(null)}
          onNavigate={setLightboxIndex}
        />
      )}
    </section>
  );
}
