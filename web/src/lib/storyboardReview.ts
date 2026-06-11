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

/** Latest ai-draft STORYBOARD batch at max version (D-43 / D-45). */
export function selectLatestStoryboardBatch(assets: AssetVersion[]): AssetVersion[] | null {
  const frames = assets.filter((a) => a.stage === "STORYBOARD" && a.branch === "ai-draft");
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
