/**
 * Wire types mirroring the API's Pydantic response models. Keep these in lockstep
 * with `api/app/routes/*` — the SPA never builds requests outside `client.ts`.
 */

export interface Project {
  id: string;
  name: string;
  status: string;
}

export interface PipelineStatus {
  project_id: string;
  run_id: string | null;
  /** Run status (PENDING/RUNNING/...) or the "IDLE" sentinel when no run exists. */
  status: string;
  current_stage: string | null;
  current_scene_index?: number | null;
  scene_count?: number | null;
  episode_id?: string | null;
  episode_number?: number | null;
  episode_title?: string | null;
  stages: string[];
  updated_at: string | null;
}

export interface Character {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  role: string | null;
  visual_traits: string | null;
  personality_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CharacterListResponse {
  project_id: string;
  characters: Character[];
}

export interface CharacterCreateResponse {
  character: Character;
}

export interface CharacterUpdateResponse {
  character: Character;
}

export interface Episode {
  id: string;
  project_id: string;
  episode_number: number;
  title: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface EpisodeListResponse {
  project_id: string;
  episodes: Episode[];
}

export interface EpisodeCreateResponse {
  episode: Episode;
}

export interface PipelineStartResponse {
  project_id: string;
  run_id: string;
  workflow_id: string;
  status: string;
  current_stage: string | null;
  scene_count: number;
  episode_id?: string | null;
  character_ids?: string[] | null;
}

export interface PipelineApproveResponse {
  project_id: string;
  run_id: string;
  approval_id: string;
  decision: string;
  stage: string;
  status: string;
  current_stage: string | null;
}

export interface PipelineRegenerateResponse {
  project_id: string;
  run_id: string;
  stage: string;
  status: string;
  current_stage: string | null;
  regenerations_used: number;
}

export interface AssetVersion {
  id: string;
  project_id: string;
  stage: string;
  version: number;
  content_hash: string;
  minio_key: string;
  is_ai_generated: boolean;
  branch: string;
  metadata_json?: Record<string, string | number | boolean> | null;
  created_at: string;
}

export interface IdeaCreateBody {
  project_id: string;
  title: string;
  paragraph: string;
  style_note?: string;
}

/** Asset stages accepted by `POST /assets` (mirrors `AssetStage` enum). */
export const ASSET_STAGES = ["IDEA", "STORY", "SCRIPT", "STORYBOARD"] as const;
export type AssetStage = (typeof ASSET_STAGES)[number];

export interface LineageNode {
  asset_id: string;
  stage: string;
  version: number;
  content_hash: string;
  is_ai_generated: boolean;
  branch: string;
  metadata: Record<string, string | number | boolean>;
  parent_asset_ids: string[];
  synthetic?: boolean | null;
}

export interface LineageEdge {
  parent_asset_id: string;
  child_asset_id: string;
}

export interface LineageResponse {
  pipeline_run_id: string;
  project_id: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
}

/** D-57 asset history version row (US-23 consumes only). */
export interface AssetHistoryVersion {
  asset_id: string;
  version: number;
  content_hash: string;
  is_ai_generated: boolean;
  branch: string;
  pipeline_run_id: string | null;
  metadata: Record<string, string | number | boolean>;
  created_at: string;
}

export interface AssetHistoryStage {
  stage: string;
  versions: AssetHistoryVersion[];
}

export interface AssetHistoryResponse {
  project_id: string;
  stages: AssetHistoryStage[];
}

/** D-64 audit trail row (US-23b). */
export interface AuditEventRow {
  id: string;
  project_id: string | null;
  pipeline_run_id: string | null;
  event_type: string;
  model_id: string | null;
  payload: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditTrailResponse {
  project_id: string;
  pipeline_run_id: string | null;
  events: AuditEventRow[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/** US-31 pipeline run summary (Phase 3B). */
export interface PipelineRunSummary {
  run_id: string;
  project_id: string;
  episode_id?: string | null;
  episode_number?: number | null;
  status: string;
  current_stage: string | null;
  temporal_workflow_id: string | null;
  asset_count: number;
  created_at: string;
  updated_at: string;
}

export interface PipelineRunListResponse {
  project_id: string;
  runs: PipelineRunSummary[];
}
