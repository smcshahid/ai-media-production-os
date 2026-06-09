# Local Setup — AIMPOS-Spark Visual

Solo-founder onboarding for local development. Steps marked _(later)_ become available as their issues land.

## Prerequisites

- Docker Desktop (Windows/macOS) or Docker Engine + Compose
- Python 3.11+ and `uv` or `pip`
- Node.js 20+ and npm
- Git

## First-time setup

1. Clone the repository and check out `main`.
2. Copy the env template:
   - `cp .env.example .env` (PowerShell: `Copy-Item .env.example .env`)
   - Fill in local-dev values. Do **not** commit `.env`.
3. Review the frozen scope: [MVP Scope Freeze](../../MVP%20Scope%20Freeze.md).
4. Review Sprint 0 plan: [Sprint 0 — Platform Skeleton](../../Sprint%200%20%E2%80%94%20Platform%20Skeleton.md).

## Running locally

- `make up` — start the Sprint-0 compose stack _(available after T-02-02)_
- `make migrate` — apply database migrations _(available after US-04)_
- `make logs-api` — tail API logs _(available after T-02-02)_

## Workflow

- One issue in progress at a time (WIP = 1).
- Branch: `feature/<issue-id>-<slug>` from latest `main`.
- Open a PR using the template; self-review against DoD; squash merge.
- See [development-workflow](../governance/development-workflow.md).
