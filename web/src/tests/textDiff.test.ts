import { describe, expect, it } from "vitest";

import { diffLines, textsDiffer } from "../lib/textDiff";

describe("textDiff", () => {
  it("detects unchanged text", () => {
    expect(textsDiffer("a\nb", "a\nb")).toBe(false);
  });

  it("marks added and removed lines", () => {
    const diff = diffLines("line one\nline two", "line one\nline three");
    expect(diff.some((row) => row.kind === "removed" && row.text === "line two")).toBe(true);
    expect(diff.some((row) => row.kind === "added" && row.text === "line three")).toBe(true);
    expect(diff.some((row) => row.kind === "same" && row.text === "line one")).toBe(true);
  });
});
