import { describe, expect, it } from "vitest";

import { resolveApiBaseUrl, resolveWebSocketBaseUrl } from "../api/baseUrl";

describe("resolveApiBaseUrl", () => {
  it("returns configured base without trailing slash", () => {
    const base = resolveApiBaseUrl();
    expect(base).not.toMatch(/\/$/);
    expect(base.length).toBeGreaterThan(0);
  });
});

describe("resolveWebSocketBaseUrl", () => {
  it("maps http base to ws scheme", () => {
    const ws = resolveWebSocketBaseUrl();
    expect(ws).toMatch(/^wss?:\/\//);
  });
});
