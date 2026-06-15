# Runbook: local development

Lightweight guide for day-to-day dev on Docker Desktop. For M1-DV (GPU/Olares), see [olares-deployment.md](./olares-deployment.md).

## Architecture (Olares hybrid)

| Component | Where it runs |
|-----------|---------------|
| **Web** | Local desktop (Vite dev server) |
| **API, Worker, Postgres, MinIO, Redis, Temporal** | Olares `aimpos-mwayolares` *(or local compose for isolated testing)* |
| **Ollama, ComfyUI** | Olares shared services (`ollamaserver-shared`, `comfyuisharev2server-shared`) |

**Recommended daily setup** — local web only, full backend on Olares:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev/start-olares-desktop.ps1
```

Sign in with the Olares API token (printed by the script, from secret `aimpos-api-env`).

Manual equivalent:

```powershell
# 1. Stop local Docker (avoids port 8000 conflict)
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env down

# 2. API tunnel
powershell -ExecutionPolicy Bypass -File scripts/dev/start-olares-tunnels.ps1 -ApiOnly

# 3. Web
cd web
$env:VITE_API_URL = "http://localhost:18000"
npm run dev
```

**Local app + Olares shared AI** (Postgres/MinIO/Redis/API/Worker on desktop, GPU on Olares):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev/start-local-app-olares-ai.ps1
```

Uses `docker-compose.olares-hybrid.yml` (no local Ollama/ComfyUI) and SSH tunnels for shared AI.

**Full local stack with GPU** (only if you have sufficient VRAM):

```powershell
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env --profile local-ai up -d
```

## Prerequisites

- Docker Desktop, Node 24+, Python 3.12+
- Copy `.env.example` → `.env` (never commit `.env`)

## Start / stop

```powershell
# from repo root
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env up -d
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env down
```

Reset data: add `-v` to `down`.

## Migrations and seed

Host venv against published DB port (see [migrations.md](./migrations.md)):

```powershell
cd api
$u = (Select-String -Path ..\.env -Pattern '^DATABASE_URL=(.*)$').Matches.Groups[1].Value -replace '@postgresql:', '@localhost:'
$env:DATABASE_URL = $u
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Seed: `docker compose -f deploy/compose/docker-compose.yml --env-file .env exec api python -m app.seed.default_project`

## Quality gates

```powershell
cd api; .\.venv\Scripts\python.exe -m pytest tests/unit -q; .\.venv\Scripts\python.exe -m ruff check app tests; .\.venv\Scripts\python.exe -m ruff format --check app tests; .\.venv\Scripts\python.exe -m mypy app
cd web; npm run build; npm run lint; npm test
```

CI mirrors these in `.github/workflows/ci-api.yml`.

## Smoke tests

| Script | Purpose | Exit codes |
|--------|---------|------------|
| `scripts/smoke/test_postgres.py` | Hermetic Postgres AC | 0 PASS |
| `scripts/smoke/test_minio.py` | Hermetic MinIO AC | 0 PASS |
| `scripts/smoke/test_ollama.py` | Ollama inference (GPU) | 0 PASS · 2 SKIP · 1 FAIL |
| `scripts/smoke/test_comfyui.py` | SDXL → MinIO (GPU) | 0 PASS · 2 SKIP · 1 FAIL |

**SKIP (exit 2)** means GPU/Ollama/ComfyUI unavailable — not a pass. Use `--require-live` on Olares for M1-DV (SKIP becomes FAIL).

```powershell
python scripts/smoke/test_postgres.py
python scripts/smoke/test_minio.py
python scripts/smoke/test_ollama.py
python scripts/smoke/test_comfyui.py
```

GPU services (`ollama`, `comfyui`) need NVIDIA runtime; CPU-only hosts expect SKIP on AI smokes.

## Service ports (dev overlay)

See README port map. Health: `curl.exe --max-time 8 http://127.0.0.1:8000/health`
