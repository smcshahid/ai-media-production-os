import { describe, expect, it } from "vitest";

import type { AssetVersion } from "../api/types";
import { batchVersion, selectLatestStoryboardBatch } from "../lib/storyboardReview";

function frame(
  partial: Partial<AssetVersion> & Pick<AssetVersion, "id" | "version">,
  frameIndex: number,
): AssetVersion {
  return {
    project_id: "p1",
    stage: "STORYBOARD",
    content_hash: "abc",
    minio_key: "k",
    is_ai_generated: true,
    branch: "ai-draft",
    metadata_json: { frame_index: frameIndex, shot_label: `Shot ${frameIndex}` },
    created_at: "2026-06-10T00:00:00Z",
    ...partial,
  };
}

describe("selectLatestStoryboardBatch", () => {
  it("returns max-version batch ordered by frame_index 1-4", () => {
    const batch = selectLatestStoryboardBatch([
      frame({ id: "v1-1", version: 1 }, 1),
      frame({ id: "v1-2", version: 1 }, 2),
      frame({ id: "v1-3", version: 1 }, 3),
      frame({ id: "v1-4", version: 1 }, 4),
      frame({ id: "v2-1", version: 2 }, 1),
      frame({ id: "v2-2", version: 2 }, 2),
      frame({ id: "v2-3", version: 2 }, 3),
      frame({ id: "v2-4", version: 2 }, 4),
    ]);
    expect(batch?.map((row) => row.id)).toEqual(["v2-1", "v2-2", "v2-3", "v2-4"]);
    expect(batchVersion(batch!)).toBe(2);
  });

  it("returns null when batch is incomplete", () => {
    expect(
      selectLatestStoryboardBatch([
        frame({ id: "a", version: 1 }, 1),
        frame({ id: "b", version: 1 }, 2),
      ]),
    ).toBeNull();
  });

  it("ignores non-storyboard rows", () => {
    const batch = selectLatestStoryboardBatch([
      frame({ id: "s1", version: 1, stage: "SCRIPT" as AssetVersion["stage"] }, 1),
      frame({ id: "f1", version: 1 }, 1),
      frame({ id: "f2", version: 1 }, 2),
      frame({ id: "f3", version: 1 }, 3),
      frame({ id: "f4", version: 1 }, 4),
    ]);
    expect(batch?.length).toBe(4);
  });
});
