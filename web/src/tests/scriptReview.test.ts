import { describe, expect, it } from "vitest";

import type { AssetVersion } from "../api/types";
import { selectLatestAiDraftScriptAsset } from "../lib/scriptReview";

function asset(partial: Partial<AssetVersion> & Pick<AssetVersion, "id">): AssetVersion {
  return {
    project_id: "p1",
    stage: "SCRIPT",
    version: 1,
    content_hash: "abc",
    minio_key: "k",
    is_ai_generated: true,
    branch: "ai-draft",
    metadata_json: null,
    created_at: "2026-06-10T00:00:00Z",
    ...partial,
  };
}

describe("selectLatestAiDraftScriptAsset", () => {
  it("picks highest version among ai-draft SCRIPT rows", () => {
    const selected = selectLatestAiDraftScriptAsset([
      asset({ id: "s1", version: 1 }),
      asset({ id: "s2", version: 3 }),
      asset({ id: "s3", version: 2 }),
    ]);
    expect(selected?.id).toBe("s2");
    expect(selected?.version).toBe(3);
  });

  it("ignores non-script and non-ai-draft rows", () => {
    const selected = selectLatestAiDraftScriptAsset([
      asset({ id: "s1", stage: "STORY", version: 9 }),
      asset({ id: "s2", branch: "human-edit", version: 5 }),
      asset({ id: "s3", version: 2 }),
    ]);
    expect(selected?.id).toBe("s3");
  });

  it("returns null when no SCRIPT ai-draft exists", () => {
    expect(selectLatestAiDraftScriptAsset([])).toBeNull();
  });
});
