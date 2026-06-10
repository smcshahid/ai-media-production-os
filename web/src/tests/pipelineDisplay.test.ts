import { describe, expect, it } from "vitest";

import {
  badgeClassForStatus,
  canStartPipeline,
  isPipelineActive,
  pipelinePollIntervalMs,
  toDisplayStatus,
} from "../lib/pipelineDisplay";

describe("pipelineDisplay", () => {
  it("maps API status to dashboard labels", () => {
    expect(toDisplayStatus("IDLE")).toBe("IDLE");
    expect(toDisplayStatus("RUNNING")).toBe("GENERATING");
    expect(toDisplayStatus("PENDING")).toBe("GENERATING");
    expect(toDisplayStatus("AWAITING_APPROVAL")).toBe("REVIEW");
    expect(toDisplayStatus("COMPLETED")).toBe("COMPLETED");
  });

  it("gates start and polling by active status", () => {
    expect(isPipelineActive("RUNNING")).toBe(true);
    expect(isPipelineActive("AWAITING_APPROVAL")).toBe(true);
    expect(canStartPipeline("COMPLETED")).toBe(true);
    expect(canStartPipeline("RUNNING")).toBe(false);
    expect(pipelinePollIntervalMs("RUNNING")).toBe(5000);
    expect(pipelinePollIntervalMs("AWAITING_APPROVAL")).toBe(5000);
    expect(pipelinePollIntervalMs("COMPLETED")).toBe(15000);
    expect(pipelinePollIntervalMs("IDLE")).toBe(15000);
  });

  it("assigns badge classes for display status", () => {
    expect(badgeClassForStatus("REVIEW")).toBe("badge--review");
    expect(badgeClassForStatus("GENERATING")).toBe("badge--generating");
    expect(badgeClassForStatus("COMPLETED")).toBe("badge--completed");
  });
});
