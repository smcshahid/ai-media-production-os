import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { isAuthenticated } from "../api/client";

/**
 * Route guard for authenticated screens. With no token in `localStorage` it
 * redirects to `/login` (preserving the attempted location); a 401 mid-session
 * is handled separately by the API client.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation();

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
}
