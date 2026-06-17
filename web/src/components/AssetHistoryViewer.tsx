import { useCallback, useEffect, useMemo, useState } from "react";

import {
  ApiError,
  getAssetContent,
  getAssetContentBlob,
  getAssetHistory,
} from "../api/client";
import type { AssetHistoryResponse, AssetHistoryVersion } from "../api/types";
import {
  formatCreatedAt,
  historyRowLabel,
  shortHash,
  stageSectionTitle,
} from "../lib/historyDisplay";
import { VersionDiffViewer } from "./VersionDiffViewer";

interface AssetHistoryViewerProps {
  projectId: string;
  pipelineRunId?: string | null;
}

type PreviewState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "text"; content: string }
  | { kind: "image"; url: string }
  | { kind: "video"; url: string; filename: string }
  | { kind: "unavailable"; message: string }
  | { kind: "error"; message: string };

const TEXT_PREVIEW_MAX = 4000;

function videoSourceLabel(metadata: Record<string, string | number | boolean>): string {
  const source = metadata.source;
  if (source === "comfyui_i2v") {
    return "ComfyUI image-to-video";
  }
  if (source === "slideshow") {
    return "Slideshow (storyboard frames)";
  }
  return typeof source === "string" ? source : "Unknown";
}

/**
 * Read-only stage-grouped asset history with inline preview, version navigation,
 * and Story/Script diff (Phase 3B / US-23 + US-30 + US-V04 UX).
 */
export function AssetHistoryViewer({ projectId, pipelineRunId }: AssetHistoryViewerProps) {
  const [history, setHistory] = useState<AssetHistoryResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<AssetHistoryVersion | null>(null);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewState>({ kind: "idle" });
  const [showDiff, setShowDiff] = useState(false);

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    setHistory(null);
    setSelected(null);
    setSelectedStage(null);
    setPreview({ kind: "idle" });
    setShowDiff(false);

    try {
      const data = await getAssetHistory(projectId, pipelineRunId);
      setHistory(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setLoadError("Project not found.");
      } else {
        setLoadError(err instanceof ApiError ? err.message : "Failed to load asset history.");
      }
    } finally {
      setLoading(false);
    }
  }, [projectId, pipelineRunId]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    return () => {
      if (preview.kind === "image" || preview.kind === "video") {
        URL.revokeObjectURL(preview.url);
      }
    };
  }, [preview]);

  const loadPreview = useCallback(async (stage: string, version: AssetHistoryVersion) => {
    if (stage === "IDEA") {
      setPreview({
        kind: "unavailable",
        message: "Content preview is not available for IDEA assets.",
      });
      return;
    }

    setPreview({ kind: "loading" });

    try {
      if (stage === "STORY" || stage === "SCRIPT") {
        const text = await getAssetContent(version.asset_id);
        setPreview({ kind: "text", content: text });
        return;
      }

      const accept =
        stage === "STORYBOARD" ? "image/png" : stage === "VIDEO" ? "video/mp4" : "application/octet-stream";
      const blob = await getAssetContentBlob(version.asset_id, accept);
      const url = URL.createObjectURL(blob);

      if (stage === "STORYBOARD") {
        setPreview({ kind: "image", url });
        return;
      }

      if (stage === "VIDEO") {
        setPreview({
          kind: "video",
          url,
          filename: `video-v${version.version}.mp4`,
        });
        return;
      }

      URL.revokeObjectURL(url);
      setPreview({ kind: "unavailable", message: "Preview is not available for this stage." });
    } catch (err) {
      setPreview({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load preview.",
      });
    }
  }, []);

  const handleSelect = useCallback(
    (stage: string, version: AssetHistoryVersion) => {
      setSelected(version);
      setSelectedStage(stage);
      setShowDiff(false);
      void loadPreview(stage, version);
    },
    [loadPreview],
  );

  const stageVersions = useMemo(() => {
    if (!history || !selectedStage) {
      return [];
    }
    return history.stages.find((group) => group.stage === selectedStage)?.versions ?? [];
  }, [history, selectedStage]);

  const selectedIndex = useMemo(() => {
    if (!selected) {
      return -1;
    }
    return stageVersions.findIndex((row) => row.asset_id === selected.asset_id);
  }, [selected, stageVersions]);

  function navigateVersion(delta: number) {
    if (!selectedStage || selectedIndex < 0) {
      return;
    }
    const next = stageVersions[selectedIndex + delta];
    if (next) {
      handleSelect(selectedStage, next);
    }
  }

  if (loading) {
    return <p className="card__hint">Loading asset history…</p>;
  }

  if (loadError) {
    return (
      <p className="page__error" role="alert">
        {loadError}
      </p>
    );
  }

  if (!history || history.stages.length === 0) {
    return <p className="card__hint">No asset versions recorded for this project.</p>;
  }

  const totalVersions = history.stages.reduce((sum, s) => sum + s.versions.length, 0);
  const diffStage =
    selectedStage === "STORY" || selectedStage === "SCRIPT" ? selectedStage : null;
  const diffVersions =
    history.stages.find((group) => group.stage === diffStage)?.versions ?? [];

  return (
    <div className="history">
      {pipelineRunId && (
        <p className="card__hint">
          Filtered to pipeline run <code className="history__mono">{pipelineRunId}</code>
        </p>
      )}
      <p className="card__hint">
        {totalVersions} version{totalVersions === 1 ? "" : "s"} across {history.stages.length}{" "}
        stage{history.stages.length === 1 ? "" : "s"}. Select a row to preview inline.
      </p>

      {history.stages.map((stageGroup) => (
        <section key={stageGroup.stage} className="history__section">
          <h3 className="history__section-title">
            {stageSectionTitle(stageGroup.stage, stageGroup.versions.length)}
          </h3>
          <ol className="history__list">
            {stageGroup.versions.map((version) => {
              const isSelected = selected?.asset_id === version.asset_id;
              return (
                <li
                  key={version.asset_id}
                  className={`history__row${isSelected ? " history__row--selected" : ""}`}
                >
                  <button
                    type="button"
                    className="history__row-button"
                    onClick={() => handleSelect(stageGroup.stage, version)}
                  >
                    <span className="history__label">
                      {historyRowLabel(stageGroup.stage, version)}
                    </span>
                    <span className="badge badge--review">{version.branch}</span>
                    {version.is_ai_generated && (
                      <span className="badge badge--review">AI</span>
                    )}
                    {stageGroup.stage === "VIDEO" && version.metadata?.source != null && (
                      <span className="badge badge--review">
                        {String(version.metadata.source)}
                      </span>
                    )}
                    <span className="history__hash">{shortHash(version.content_hash)}</span>
                  </button>
                </li>
              );
            })}
          </ol>
        </section>
      ))}

      {selected && selectedStage && (
        <div className="history__panel" aria-live="polite">
          <div className="history__panel-header">
            <h3 className="history__panel-title">Version metadata</h3>
            <div className="history__nav">
              <button
                type="button"
                className="button"
                disabled={selectedIndex <= 0}
                onClick={() => navigateVersion(-1)}
              >
                ← Prev
              </button>
              <button
                type="button"
                className="button"
                disabled={selectedIndex < 0 || selectedIndex >= stageVersions.length - 1}
                onClick={() => navigateVersion(1)}
              >
                Next →
              </button>
            </div>
          </div>

          <dl className="history__meta">
            <div>
              <dt>Stage</dt>
              <dd>{selectedStage}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{selected.version}</dd>
            </div>
            <div>
              <dt>Asset ID</dt>
              <dd className="history__mono">{selected.asset_id}</dd>
            </div>
            <div>
              <dt>Content hash</dt>
              <dd className="history__mono">{selected.content_hash}</dd>
            </div>
            <div>
              <dt>Branch</dt>
              <dd>{selected.branch}</dd>
            </div>
            <div>
              <dt>AI generated</dt>
              <dd>{selected.is_ai_generated ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{formatCreatedAt(selected.created_at)}</dd>
            </div>
            <div>
              <dt>Pipeline run</dt>
              <dd className="history__mono">{selected.pipeline_run_id ?? "—"}</dd>
            </div>
            {selectedStage === "STORYBOARD" && selected.metadata?.frame_index != null && (
              <div>
                <dt>Frame index</dt>
                <dd>{String(selected.metadata.frame_index)}</dd>
              </div>
            )}
            {selectedStage === "VIDEO" && selected.metadata?.source != null && (
              <>
                <div>
                  <dt>Video source</dt>
                  <dd>{videoSourceLabel(selected.metadata)}</dd>
                </div>
                {selected.metadata.fallback_reason != null && (
                  <div>
                    <dt>Fallback reason</dt>
                    <dd>{String(selected.metadata.fallback_reason)}</dd>
                  </div>
                )}
              </>
            )}
          </dl>

          {diffStage && diffVersions.length >= 2 && (
            <div className="history__diff-toggle">
              <button type="button" className="button" onClick={() => setShowDiff((v) => !v)}>
                {showDiff ? "Hide version diff" : "Compare versions"}
              </button>
            </div>
          )}

          {showDiff && diffStage && (
            <VersionDiffViewer stage={diffStage} versions={diffVersions} />
          )}

          {preview.kind === "loading" && <p className="card__hint">Loading preview…</p>}
          {preview.kind === "unavailable" && (
            <p className="card__hint" role="note">
              {preview.message}
            </p>
          )}
          {preview.kind === "error" && (
            <p className="page__error" role="alert">
              {preview.message}
            </p>
          )}
          {preview.kind === "text" && (
            <pre className="history__preview-text">
              {preview.content.length > TEXT_PREVIEW_MAX
                ? `${preview.content.slice(0, TEXT_PREVIEW_MAX)}…`
                : preview.content}
            </pre>
          )}
          {preview.kind === "image" && (
            <img
              className="history__preview-image"
              src={preview.url}
              alt={`Storyboard frame preview v${selected.version}`}
            />
          )}
          {preview.kind === "video" && (
            <div className="history__video-wrap">
              <video
                className="history__preview-video"
                src={preview.url}
                controls
                playsInline
                preload="metadata"
              />
              <a className="history__download-link" href={preview.url} download={preview.filename}>
                Download video (v{selected.version})
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
