import type { ApiError } from "../api/client";

/** Map API errors to creator-friendly review messages (Phase 3B / WP-5). */
export function formatReviewActionError(err: unknown, fallback: string): string {
  if (err && typeof err === "object" && "status" in err && "message" in err) {
    const apiErr = err as ApiError;
    return apiErr.message || fallback;
  }
  if (err instanceof Error) {
    return err.message || fallback;
  }
  return fallback;
}
