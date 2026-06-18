import type { AssetVersion } from "../api/types";

export const STORYBOARD_FRAME_COUNT = 4;

function frameIndex(asset: AssetVersion): number {
  const raw = asset.metadata_json?.frame_index;
  if (typeof raw === "number") {
    return raw;
  }
  if (typeof raw === "string") {
    return parseInt(raw, 10);
  }
  return 0;
}

function sceneIndex(asset: AssetVersion): number {
  const raw = asset.metadata_json?.scene_index;
  if (typeof raw === "number") {
    return raw;
  }
  if (typeof raw === "string") {
    return parseInt(raw, 10);
  }
  return 1;
}

/** Latest ai-draft STORYBOARD batch at max version for a scene (D-43 / D-76). */
export function selectLatestStoryboardBatch(
  assets: AssetVersion[],
  targetSceneIndex = 1,
): AssetVersion[] | null {
  const frames = assets.filter(
    (a) =>
      a.stage === "STORYBOARD" &&
      a.branch === "ai-draft" &&
      sceneIndex(a) === targetSceneIndex,
  );
  if (frames.length === 0) {
    return null;
  }
  const maxVersion = frames.reduce((max, row) => Math.max(max, row.version), 0);
  const batch = frames
    .filter((row) => row.version === maxVersion)
    .sort((a, b) => frameIndex(a) - frameIndex(b));
  if (batch.length !== STORYBOARD_FRAME_COUNT) {
    return null;
  }
  for (let i = 0; i < STORYBOARD_FRAME_COUNT; i += 1) {
    if (frameIndex(batch[i]!) !== i + 1) {
      return null;
    }
  }
  return batch;
}

export function batchVersion(frames: AssetVersion[]): number {
  return frames[0]?.version ?? 0;
}

export function distinctSceneIndices(assets: AssetVersion[]): number[] {
  const indices = new Set<number>();
  for (const asset of assets) {
    if (asset.stage === "STORYBOARD" || asset.stage === "VIDEO") {
      indices.add(sceneIndex(asset));
    }
  }
  return [...indices].sort((a, b) => a - b);
}
