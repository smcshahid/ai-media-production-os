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
  stages: string[];
  updated_at: string | null;
}

export interface PipelineStartResponse {
  project_id: string;
  run_id: string;
  workflow_id: string;
  status: string;
  current_stage: string | null;
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
  metadata_json?: Record<string, string> | null;
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
