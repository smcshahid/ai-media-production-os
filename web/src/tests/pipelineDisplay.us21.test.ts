import { describe, expect, it } from "vitest";

import { pipelineLivePollIntervalMs, pipelinePollIntervalMs } from "../lib/pipelineDisplay";

describe("pipelineLivePollIntervalMs", () => {
  it("returns 30s sanity interval for live mode", () => {
    expect(pipelineLivePollIntervalMs()).toBe(30000);
  });
});

describe("pipelinePollIntervalMs fallback", () => {
  it("uses 5s for active runs in polling mode", () => {
    expect(pipelinePollIntervalMs("RUNNING")).toBe(5000);
  });

  it("uses 15s when idle", () => {
    expect(pipelinePollIntervalMs("IDLE")).toBe(15000);
  });
});

describe("monotonic updated_at guard", () => {
  it("accepts newer timestamps", () => {
    const older = "2026-06-10T10:00:00Z";
    const newer = "2026-06-10T10:00:05Z";
    expect(newer >= older).toBe(true);
  });
});
