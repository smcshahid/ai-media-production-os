import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, clearToken, getToken, listProjects, setToken } from "../api/client";

describe("api client", () => {
  beforeEach(() => {
    clearToken();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    clearToken();
    vi.restoreAllMocks();
  });

  it("attaches the Bearer token from localStorage", async () => {
    setToken("secret-token");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify([]), { status: 200 }));

    await listProjects();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const init = fetchMock.mock.calls[0][1];
    const headers = new Headers(init?.headers);
    expect(headers.get("Authorization")).toBe("Bearer secret-token");
  });

  it("clears the token and throws ApiError on 401", async () => {
    setToken("bad-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Unauthorized" }), { status: 401 }),
    );

    await expect(listProjects()).rejects.toBeInstanceOf(ApiError);
    expect(getToken()).toBeNull();
  });
});
