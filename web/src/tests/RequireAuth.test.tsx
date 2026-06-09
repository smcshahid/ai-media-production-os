import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { clearToken, setToken } from "../api/client";
import { RequireAuth } from "../components/RequireAuth";

function renderGuarded(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>login screen</div>} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <div>protected content</div>
            </RequireAuth>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RequireAuth", () => {
  afterEach(() => clearToken());

  it("redirects to /login when no token is present", () => {
    clearToken();
    renderGuarded("/");
    expect(screen.getByText("login screen")).toBeInTheDocument();
  });

  it("renders children when a token is present", () => {
    setToken("test-token");
    renderGuarded("/");
    expect(screen.getByText("protected content")).toBeInTheDocument();
  });
});
