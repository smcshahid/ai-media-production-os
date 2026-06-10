import { describe, expect, it } from "vitest";

import { selectLatestStoryAsset } from "../lib/storyReview";
import type { AssetVersion } from "../api/types";

function asset(partial: Partial<AssetVersion> & Pick<AssetVersion, "id" | "version" | "stage">): AssetVersion {
  return {
    project_id: "p1",
    content_hash: "abc",
    minio_key: "k",
    is_ai_generated: true,
    branch: "ai-draft",
    created_at: "2026-01-01T00:00:00Z",
    ...partial,
  };
}

describe("storyReview", () => {
  it("selects the highest STORY version", () => {
    const assets: AssetVersion[] = [
      asset({ id: "a1", stage: "IDEA", version: 1 }),
      asset({ id: "s1", stage: "STORY", version: 1, branch: "ai-draft" }),
      asset({ id: "s2", stage: "STORY", version: 2, branch: "human-edit", is_ai_generated: false }),
    ];
    const latest = selectLatestStoryAsset(assets);
    expect(latest?.id).toBe("s2");
    expect(latest?.version).toBe(2);
  });

  it("returns null when no STORY assets exist", () => {
    expect(selectLatestStoryAsset([asset({ id: "i1", stage: "IDEA", version: 1 })])).toBeNull();
  });
});
