# web/ — React SPA (Vite + TypeScript)

Web console for AIMPOS-Spark Visual.

## Service boundary (non-negotiable, coding-standards §23)

- Communicates with `api/` REST **only** — never Temporal, Ollama, or ComfyUI.
- All backend calls go through `src/api/client.ts`.
- Attaches Bearer token (US-25). Desktop layout ≥ 768px.

## Folder map (Repository Structure §4.6)

| Path | Purpose | Lands in |
|------|---------|----------|
| `src/routes/` | Page per screen (Login, Dashboard, Assets, Audit) | US-26, US-25, US-10 |
| `src/components/layout/` | AppShell, NavBar | US-26 |
| `src/components/pipeline/` | StageStepper, StatusBadge | US-10 |
| `src/api/` | Typed API client + token injection | US-26, US-25 |
| `src/hooks/` | Polling hooks | US-10 |
| `src/tests/` | Component/hook tests | per issue |

`package.json` (React, Vite, TypeScript, ESLint, Prettier) is introduced with US-26.
