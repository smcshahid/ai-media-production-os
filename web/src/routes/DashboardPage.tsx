import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  ApiError,
  createEpisode,
  listAssets,
  listEpisodes,
  startPipeline,
  listProjects,
} from "../api/client";
import type { AssetVersion, Episode, Project } from "../api/types";
import { IdeaCaptureForm } from "../components/IdeaCaptureForm";
import { CharacterPanel } from "../components/CharacterPanel";
import { PipelineConnectionIndicator } from "../components/PipelineConnectionIndicator";
import { PipelineRunHistory } from "../components/PipelineRunHistory";
import { Stepper } from "../components/Stepper";
import { usePipelineStatus } from "../hooks/usePipelineStatus";
import {
  badgeClassForStatus,
  canStartPipeline,
  toDisplayStatus,
} from "../lib/pipelineDisplay";

const IDLE_STAGES = ["IDEA", "STORY", "SCRIPT", "STORYBOARD", "VIDEO"];

const STAGE_LABELS: Record<string, string> = {
  IDEA: "Idea",
  STORY: "Story",
  SCRIPT: "Script",
  STORYBOARD: "Storyboard",
  VIDEO: "Video",
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
  const [sceneCount, setSceneCount] = useState(1);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [selectedEpisodeId, setSelectedEpisodeId] = useState<string | "legacy">("legacy");
  const [episodeMode, setEpisodeMode] = useState(false);
  const [creatingEpisode, setCreatingEpisode] = useState(false);
  const [selectedCharacterIds, setSelectedCharacterIds] = useState<string[]>([]);
  const [ideaVersion, setIdeaVersion] = useState<AssetVersion | null>(null);

  const refreshIdea = useCallback(async (projectId: string) => {
    const assets = await listAssets(projectId);
    setIdeaVersion(latestIdeaVersion(assets));
  }, []);

  const refreshEpisodes = useCallback(async (projectId: string) => {
    const response = await listEpisodes(projectId);
    setEpisodes(response.episodes);
    if (response.episodes.length > 0) {
      setEpisodeMode(true);
    }
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
          await refreshEpisodes(first.id);
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
  }, [refreshIdea, refreshEpisodes]);

  const activeEpisodeId =
    selectedEpisodeId === "legacy" ? null : selectedEpisodeId;

  const { status: pipeline, error: statusError, loading, connectionMode, refresh } = usePipelineStatus(
    project?.id ?? null,
    activeEpisodeId,
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
      await startPipeline(
        project.id,
        sceneCount,
        activeEpisodeId,
        selectedCharacterIds.length > 0 ? selectedCharacterIds : null,
      );
      refresh();
    } catch (err) {
      setStartError(err instanceof ApiError ? err.message : "Failed to start pipeline.");
    } finally {
      setStarting(false);
    }
  }

  async function handleCreateEpisode() {
    if (!project) {
      return;
    }
    setCreatingEpisode(true);
    setStartError(null);
    try {
      const title = `Episode ${episodes.length + 1}`;
      const created = await createEpisode(project.id, title);
      await refreshEpisodes(project.id);
      setSelectedEpisodeId(created.episode.id);
      setEpisodeMode(true);
    } catch (err) {
      setStartError(err instanceof ApiError ? err.message : "Failed to create episode.");
    } finally {
      setCreatingEpisode(false);
    }
  }

  const currentSceneIndex = pipeline?.current_scene_index ?? null;
  const runSceneCount = pipeline?.scene_count ?? null;

  const statusLine = (() => {
    if (loading && !pipeline) {
      return "Loading pipeline status…";
    }
    if (displayStatus === "IDLE") {
      return "No pipeline run yet.";
    }
    const episodeSuffix =
      pipeline?.episode_number != null
        ? ` · Episode ${pipeline.episode_number}`
        : "";
    const sceneSuffix =
      currentSceneIndex && runSceneCount && runSceneCount > 1
        ? ` (scene ${currentSceneIndex} of ${runSceneCount})`
        : "";
    if (displayStatus === "GENERATING" && currentStage) {
      return `Generating ${STAGE_LABELS[currentStage] ?? currentStage}${episodeSuffix}${sceneSuffix}…`;
    }
    if (displayStatus === "REVIEW" && currentStage) {
      return `${STAGE_LABELS[currentStage] ?? currentStage}${episodeSuffix}${sceneSuffix} ready for your review.`;
    }
    if (displayStatus === "COMPLETED") {
      return `Pipeline completed${episodeSuffix} — all stages approved.`;
    }
    return `Status: ${displayStatus}${episodeSuffix}`;
  })();

  return (
    <section className="page">
      <header className="page__header">
        <h1 className="page__title">{project?.name ?? "AIMPOS Spark Demo"}</h1>
        <div className="page__header-badges">
          <span className={`badge ${badgeClassForStatus(displayStatus)}`}>{displayStatus}</span>
          {project && <PipelineConnectionIndicator mode={connectionMode} />}
        </div>
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
        <h2 className="card__title">Episodes</h2>
        <p className="card__hint">
          Pilot: create episodes under this project, then start a pipeline scoped to one episode.
        </p>
        <div className="card__actions">
          <button
            type="button"
            className="button"
            disabled={creatingEpisode || !project}
            onClick={() => void handleCreateEpisode()}
          >
            {creatingEpisode ? "Creating…" : "New Episode"}
          </button>
        </div>
        {episodeMode && episodes.length > 0 && (
          <div className="card__field">
            <label htmlFor="episode-select" className="card__hint">
              Active episode
            </label>
            <select
              id="episode-select"
              className="input"
              value={selectedEpisodeId}
              onChange={(event) => setSelectedEpisodeId(event.target.value)}
            >
              <option value="legacy">Legacy (no episode)</option>
              {episodes.map((episode) => (
                <option key={episode.id} value={episode.id}>
                  Episode {episode.episode_number}
                  {episode.title ? ` — ${episode.title}` : ""} ({episode.status})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {project && (
        <CharacterPanel
          projectId={project.id}
          selectedIds={selectedCharacterIds}
          onSelectionChange={setSelectedCharacterIds}
        />
      )}

      <div className="card">
        <h2 className="card__title">Pipeline</h2>
        <p className="dashboard__status-line">{statusLine}</p>
        {!hasIdea && (
          <p className="dashboard__guidance" role="note">
            Save your idea above before starting the pipeline.
          </p>
        )}
        <Stepper stages={stages} currentStage={currentStage} status={apiStatus} />
        {canStartPipeline(apiStatus) && (
          <div className="card__field">
            <label htmlFor="scene-count" className="card__hint">
              Scenes per run (pilot: 1–3)
            </label>
            <select
              id="scene-count"
              className="input"
              value={sceneCount}
              onChange={(event) => setSceneCount(Number(event.target.value))}
              disabled={starting}
            >
              <option value={1}>1 scene (classic)</option>
              <option value={2}>2 scenes</option>
              <option value={3}>3 scenes</option>
            </select>
          </div>
        )}
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

      {project && (
        <div className="card">
          <h2 className="card__title">Run history</h2>
          <p className="card__hint">
            Past pipeline runs with status, asset counts, and links to audit and history views.
          </p>
          <PipelineRunHistory projectId={project.id} activeRunId={pipeline?.run_id} />
        </div>
      )}
    </section>
  );
}
