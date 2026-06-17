# Runbook: local development

Day-to-day dev: **local app + Olares shared AI (24GB GPU)**. Open the web UI and run the pipeline — Ollama and ComfyUI always go through Olares.

For full Olares backend deployment, see [olares-deployment.md](./olares-deployment.md).

## Architecture (default)

| Component | Where it runs |
|-----------|---------------|
| **Web, API, Worker, Postgres, MinIO, Redis, Temporal** | Local Docker (desktop) |
| **Ollama, ComfyUI** | Olares shared services via SSH tunnels (`localhost:11434`, `localhost:8190`) |

Storyboard images use **Flux.1-dev** (`flux_storyboard.json`). Video uses **WAN 2.2 i2v** when weights are present on Olares.

## Start (one command)

```powershell
# from repo root — first time: cp .env.example .env
make up-dev
```

This automatically:

1. Ensures SSH tunnels to Olares Ollama + ComfyUI are up (`scripts/dev/ensure-olares-ai-tunnels.ps1`)
2. Applies Alembic migrations and validates revision 0003 (`scripts/dev/ensure-db-migrated.ps1`)
3. Starts the local app stack with worker hard-wired to Olares (`docker-compose.dev.yml`)
4. Rebuilds the worker/api/web images (so workflow JSON and API changes are picked up)

Then open **http://localhost:5173**, sign in with `AIMPOS_API_TOKEN` from `.env`, and run the pipeline.

After pulling code changes that touch workflows or worker logic:

```powershell
make up-dev-build
```

## Stop / reset

```powershell
make down
# reset volumes: docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env down -v
```

## Opt-in: local GPU instead of Olares

Only if you have sufficient local VRAM and want in-compose Ollama + ComfyUI:

```powershell
make up-dev-local-ai
```

Uses SDXL storyboards and disables WAN i2v (local ComfyUI container is SDXL-only).

## Olares desktop mode (web-only, API on Olares)

Separate path — local Vite dev server + Olares API tunnel:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev/start-olares-desktop.ps1
```

Set `VITE_API_URL=http://localhost:18000` for that mode.

## Olares hosted app (Phase 3C — no local dev required)

AIMPOS web runs on Olares as a first-class application entrance. Deploy and verify:

```powershell
# See deploy/olares/aimpos/README.md for full image build + helm deploy steps
make verify-phase3c-olares
```

Open from the Olares launcher (Application `aimpos-mwayolares-aimpos`). Sign in with the API token from the cluster `aimpos-api-env` secret.

## Prerequisites

- Docker Desktop
- SSH to Olares (`olares@10.0.0.34` by default; override `OLARES_HOST` in `.env`)
- Copy `.env.example` → `.env` (never commit `.env`)

## Migrations and seed

See [migrations.md](./migrations.md). Seed:

```powershell
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env exec api python -m app.seed.default_project
```

## Verify worker is on Olares

```powershell
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env exec worker sh -c 'echo OLLAMA=$OLLAMA_HOST COMFYUI=$COMFYUI_HOST WORKFLOW=$COMFYUI_WORKFLOW I2V=$VIDEO_I2V_ENABLED'
```

Expected:

```
OLLAMA=http://host.docker.internal:11434
COMFYUI=http://host.docker.internal:8190
WORKFLOW=flux_storyboard.json
I2V=true
```

## Verify database migrations (WP-3)

```powershell
make verify-bootstrap
# or: powershell -ExecutionPolicy Bypass -File scripts/dev/ensure-db-migrated.ps1
```

Expected: Alembic revision `0003` and STORYBOARD partial unique indexes present.

## Audit trail (US-23b)

Open **http://localhost:5173/audit** or `GET /audit?project_id=<uuid>` for the append-only event log.

## Quality gates

```powershell
cd api; .\.venv\Scripts\python.exe -m pytest tests/unit -q
cd web; npm run build; npm run lint; npm test
cd worker; python -m pytest tests/unit -q
```

## Service ports (dev overlay)

| Service | Host port |
|---------|-----------|
| `web` | 5173 |
| `api` | 8000 |
| `postgresql` | 5432 |
| `minio` | 9000 / 9001 |
| `temporal-ui` | 8080 |
| Olares Ollama (tunnel) | 11434 |
| Olares ComfyUI (tunnel) | 8190 |

Health: `curl http://127.0.0.1:8000/health`
