import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { clearToken } from "../../api/client";

/**
 * Authenticated layout: a persistent nav bar (Dashboard, Assets, Audit) plus the
 * routed page via `<Outlet />`. Rendered behind `RequireAuth`, so reaching it
 * implies a token is present.
 */
export function AppShell() {
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <header className="app-shell__bar">
        <span className="app-shell__brand">AIMPOS Spark</span>
        <nav className="app-shell__nav">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/assets">Assets</NavLink>
          <NavLink to="/history">History</NavLink>
          <NavLink to="/export">Export</NavLink>
          <NavLink to="/audit">Audit</NavLink>
        </nav>
        <button type="button" className="app-shell__logout" onClick={handleLogout}>
          Log out
        </button>
      </header>
      <main className="app-shell__main">
        <Outlet />
      </main>
    </div>
  );
}
