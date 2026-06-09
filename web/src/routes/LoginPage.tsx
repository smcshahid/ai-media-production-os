import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError, clearToken, listProjects, setToken } from "../api/client";

/**
 * Token entry (Sprint 0 plan §4.7). The Bearer token is validated by calling a
 * protected endpoint: a 200 stores it and redirects to the dashboard; a 401
 * shows an error and leaves the user on `/login`.
 */
export function LoginPage() {
  const navigate = useNavigate();
  const [token, setTokenValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = token.trim();
    if (!trimmed) {
      setError("Enter an API token.");
      return;
    }

    setError(null);
    setSubmitting(true);
    setToken(trimmed);
    try {
      await listProjects();
      navigate("/", { replace: true });
    } catch (err) {
      clearToken();
      if (err instanceof ApiError && err.status === 401) {
        setError("Invalid token. Check the value and try again.");
      } else {
        setError("Could not reach the API. Is it running?");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login">
      <form className="login__card" onSubmit={handleSubmit}>
        <h1 className="login__title">AIMPOS Spark</h1>
        <p className="login__subtitle">Sign in with your API token to continue.</p>

        <label className="login__label" htmlFor="token">
          API token
        </label>
        <input
          id="token"
          type="password"
          className="login__input"
          value={token}
          onChange={(event) => setTokenValue(event.target.value)}
          autoComplete="off"
          autoFocus
        />

        {error && (
          <p className="login__error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="login__submit" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
