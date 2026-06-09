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

export interface AssetVersion {
  id: string;
  project_id: string;
  stage: string;
  version: number;
  content_hash: string;
  minio_key: string;
  is_ai_generated: boolean;
  branch: string;
  created_at: string;
}

/** Asset stages accepted by `POST /assets` (mirrors `AssetStage` enum). */
export const ASSET_STAGES = ["IDEA", "STORY", "SCRIPT", "STORYBOARD"] as const;
export type AssetStage = (typeof ASSET_STAGES)[number];
