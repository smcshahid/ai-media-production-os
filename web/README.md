# web/ — AIMPOS-Spark Visual Console (React SPA)

React + TypeScript single-page app (Vite). Sprint 0 ships four routes —
`/login`, `/` (Dashboard), `/assets`, `/audit` — wired to the API's Bearer-token
REST surface.

## Stack

- React 19 + TypeScript (strict)
- Vite 7 (dev server + build)
- React Router 7
- Vitest + Testing Library (colocated tests in `src/tests/`)
- ESLint (flat config) + Prettier

## Local development

```bash
cd web
npm install
npm run dev          # http://localhost:5173
```

The app talks to the API at `VITE_API_URL` (default `http://localhost:8000`).
The API must allow the SPA origin via `CORS_ORIGINS` (default
`http://localhost:5173`). Bring the backend up with `make up-dev` from the repo
root first.

### Signing in

Authentication is a static Bearer token (US-25). Enter the value of
`AIMPOS_API_TOKEN` (see root `.env`) on the `/login` screen. The token is stored
in `localStorage`; a 401 from any request clears it and returns you to `/login`.

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Vite dev server with HMR on `:5173` |
| `npm run build` | Type-check (`tsc --noEmit`) then production build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | ESLint over `src/` |
| `npm run format` | Prettier write |
| `npm test` | Vitest unit/component tests |

## Architecture

- `src/api/client.ts` — the **only** place that calls `fetch`. Attaches the
  Bearer token, normalizes errors (`ApiError`), and redirects to `/login` on 401.
  Components import typed endpoint helpers (`listProjects`, `uploadAsset`, …).
- `src/components/` — reusable UI (`layout/AppShell`, `Stepper`, `RequireAuth`).
- `src/hooks/usePipelineStatus.ts` — polls `GET /pipeline/status` (MVP defers
  WebSockets).
- `src/routes/` — one component per screen.

## Container

```bash
# from repo root (build context = root)
docker build -f web/Dockerfile -t aimpos-web .
```

Multi-stage: Node build → nginx serve with SPA history fallback. In compose the
`web` service is published on `5173` by the dev overlay.
