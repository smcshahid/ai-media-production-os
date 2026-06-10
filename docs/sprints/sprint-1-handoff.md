# Sprint 1 — Infrastructure Validation: Agent Handoff

**Governance:** SCR-2026-001 approved in principle (2026-06-09); gates per **D-31** (`S1-SW` + `M1-DV`).

**Audience:** the engineering agent picking up Sprint 1.
**Read this first, in full.** Then read [`sprint-0-briefing.md`](./sprint-0-briefing.md) (what already exists), skim the tail of [`Sprint0_Status.md`](../../Sprint0_Status.md) and recent [`DECISIONS.md`](../../DECISIONS.md) entries. Scope/AC are frozen in [`Sprint 0 — Platform Skeleton.md`](../../Sprint%200%20%E2%80%94%20Platform%20Skeleton.md) §3.2/§4 (Phase B) and [`Sprint Reclassification.md`](../../Sprint%20Reclassification.md).

You are the **Lead Engineer** for AIMPOS-Spark. Optimize for safe, verified progress in dependency order. Follow the approved architecture, governance, and coding standards. **Self-review and verify live before presenting results.**

---

## 0. TL;DR — your prime directive

> **Sprint 1 = "Infrastructure Validation": stand up the full 9-service stack, deploy on Olares, and prove the GPU/AI path works (Ollama + ComfyUI smoke).** It is **not** user features.
>
> **Before you build US-02/US-06, answer one question honestly: do you have GPU + Olares access in this environment?** If not, most of Sprint 1 **cannot proceed safely** — do the parts that can (compose authoring, scripts, docs, CI, tech-debt), and clearly report the hardware blocker instead of faking it. The frozen plan has a **failure protocol** for exactly this (stub PNGs, document as known limitation). Do not pretend a GPU smoke passed.

---

## 1. Current state (start of Sprint 1)

- **Sprint 0 is complete and merged to `main`** (PRs #74, #75). 23 S0 issues closed; only EPIC-06 (multi-sprint governance) stays open.
- **Repo:** clean, on `main`, linear history. Build context for `api/` and `web/` Dockerfiles is the **repo root**.
- **Running stack (Sprint-0, 5 services):** postgresql, minio (+ one-shot minio-init), redis, api, web — all healthy via `make up-dev` (or the compose commands below). Pristine data: one seeded `AIMPOS Spark Demo` project, empty assets.
- **What works today:** Login (Bearer token), `GET /projects`, `POST/GET /assets`, `GET /pipeline/status` (idle), `GET /health`, the React SPA (`/login`, `/`, `/assets`, `/audit`).
- **Environment:** Windows + **PowerShell**, Docker Desktop, Node 24, Python 3.12. There is an API venv at `api/.venv`. **There is no CI yet (TD-21)** — you are the CI.

---

## 2. Sprint 1 scope (class B — work these in order)

| # | Issue | What "done" means | Needs GPU/Olares? |
|---|-------|-------------------|:---:|
| #44 | **T-02-01** Write `docker-compose.yml` for all 9 services | Compose defines the full stack (adds worker, temporal[+UI], ollama, comfyui to today's 5) on the internal network; dev overlay publishes ports; healthchecks; `docker compose config` valid | Authoring: no · Running ollama/comfyui: **yes** |
| #47 | **T-02-04** Pin Ollama model `llama3.1:13b` in compose init | Model pinned + pulled by an init step; **D-02** recorded (model + VRAM justification) | Pull/run: **yes** |
| #60 | **T-06-01** Ollama connectivity test script | Script hits Ollama and gets a completion; deterministic, stdlib-only style like `scripts/smoke/test_*.py` | **yes** (live) |
| #61 | **T-06-02** Pin + test ComfyUI SDXL workflow JSON | Workflow pinned under `configs/comfyui/workflows/`; smoke runs it to a PNG; **D-03** recorded | **yes** (live) |
| #62 | **T-06-03** Document GPU sequencing rule in `worker/README.md` | **D-08**: never run Ollama and ComfyUI concurrently (VRAM); documented | no |
| #48 | **T-02-05** Document Olares deployment in README | Deploy steps for Olares (compose → Olares Docker mode) | no (docs) |
| #49 | **T-02-06** Verify zero egress during compose startup | Prove no outbound network during normal startup (governance: zero-egress) | partial |
| #7 / #3 / #2 / #1 | **US-06 / US-02 / FEAT-INFRA / EPIC-01** | Roll up the above; close when full stack + GPU validated on Olares | **yes** |
| #69, #70, #71 | tech-debt (P1) | Least-privilege Postgres env (drop blanket `env_file`); hermetic Postgres smoke test; Sprint-0 service port-map in README | no |
| (TD-21) | CI workflow | **Do this early.** `ci-api.yml` (+ a web job): ruff/format/mypy/pytest and `tsc`/vite build/eslint/vitest on PRs | no |

**Recommended order:** (1) **CI first** (TD-21) so every later PR is gated → (2) tech-debt that's pure-software (#69/#70/#71, GPU sequencing docs #62) → (3) full compose authoring (#44) validated with `docker compose config` → (4) **gate on GPU/Olares availability**; if present, do #47/#60/#61/#49/#48 and close US-06/US-02; if absent, stop and report.

### The 9 services (target stack)
Today's 5 — `postgresql`, `minio` (+`minio-init`), `redis`, `api`, `web` — plus Sprint-1 additions: **`worker`** (Temporal worker stub), **`temporal`** (+ temporal UI), **`ollama`** (LLM), **`comfyui`** (image gen). Confirm the exact list against T-02-01's AC and `Repository Structure.md` before writing it.

### GPU rule you must honor (D-08)
**Never run Ollama and ComfyUI concurrently** — single-GPU VRAM won't hold both. Sequence them. Document this in `worker/README.md` and make any smoke test load one, unload, then the other.

---

## 3. How to run things here (copy-paste, PowerShell-safe)

```powershell
# from repo root
cp .env.example .env                 # first time only
# Start stack (dev overlay publishes host ports). 'make' is NOT installed here — use compose directly:
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env up -d
# Stop (keep data):
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env down
# Pristine reset (wipe volumes), then re-migrate + re-seed:
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env down -v
```

**Migrate (the api image excludes `alembic/`, TD-17) — run from the host venv against the published DB port:**
```powershell
cd api
$u = (Select-String -Path ..\.env -Pattern '^DATABASE_URL=(.*)$').Matches.Groups[1].Value -replace '@postgresql:', '@localhost:'
$env:DATABASE_URL = $u
.\.venv\Scripts\python.exe -m alembic upgrade head
```
**Seed:** `docker compose -f deploy/compose/docker-compose.yml --env-file .env exec api python -m app.seed.default_project`

**Quality gates (run BEFORE every PR — there is no CI yet):**
```powershell
# API
cd api ; .\.venv\Scripts\python.exe -m pytest tests/unit -q ; .\.venv\Scripts\python.exe -m ruff check app tests ; .\.venv\Scripts\python.exe -m ruff format --check app tests ; .\.venv\Scripts\python.exe -m mypy app
# Web
cd web ; npm run build ; npm run lint ; npm test
```

---

## 4. Lessons learned in Sprint 0 (read these — they cost real time)

1. **PowerShell is not bash. This bit us repeatedly.**
   - `&&` is **not** a valid separator → use `;` or separate calls.
   - `<` and `>` are **redirection operators** even inside many strings → a `pip install "x>=2.0,<3.0"` passed through `docker run sh -c` created a junk file `=2.0,` and failed with "cannot open 3.0". Avoid `<`/`>` on the command line; prefer host venvs or requirements files.
   - **Commit messages:** heredocs don't work. Write the message to a temp file and `git commit -F file`, then delete it.
   - **`gh ... --jq '...'` with quotes/spaces breaks** under PowerShell. Use `--json` and pipe to `ConvertFrom-Json`, then format in PowerShell.
2. **IPv6 `localhost` is a trap.** Inside containers `localhost` can resolve to `::1` while servers bind IPv4 → "connection refused". The web healthcheck failed this way (fixed by probing `127.0.0.1`). On the host, `Invoke-WebRequest http://localhost:...` **hangs**; use `curl.exe --max-time 8 http://127.0.0.1:...`. (The user twice asked "are you stuck?" — it was always IWR/IPv6, never a real hang.)
3. **Windows + psycopg async:** `psycopg` rejects the default `ProactorEventLoop`. Integration tests set `WindowsSelectorEventLoopPolicy` in `tests/integration/conftest.py` (no-op on Linux/CI). Keep this when adding integration tests.
4. **No CI = you must run all gates locally** every time. A green local run is the only gate. Add CI early in Sprint 1.
5. **Frozen docs outrank task cards.** Where they conflicted (e.g. `name` vs `title`, routes `/login..` vs `/review`), the Sprint plan won and the decision was recorded. Reconcile, don't guess; record a `D-XX`.
6. **Scope discipline pays off.** Sprint 0 had real planning gaps (no task for `POST/GET /assets`, `/pipeline/status`, CORS). The right move was to fill the *required* gap, record it as a decision + tech-debt, and **not** invent extra scope. Don't over-scaffold.
7. **Branch protection on `main`:** PRs required (0 approvals needed), **linear history required** → merge with `--rebase` (or `--squash`), never a merge commit. `enforce_admins` is off.
8. **Build context is the repo root** for `api/`/`web/` images (so `packages/` is visible). New images (worker, etc.) likely follow the same pattern.
9. **Verify live, not just unit tests.** Every Sprint-0 increment was checked against the running stack (curl + a real browser walkthrough), which caught the healthcheck bug that unit tests never would.

---

## 5. How you should behave (rules derived from the lessons)

- **Don't get stuck — diagnose and switch.** If a command hangs or fails twice the same way, stop repeating it; change approach (different tool, `127.0.0.1`, timeout, host venv). Always add `--max-time`/timeouts to network calls.
- **Prefer the specialized tools** (read/edit/grep) over shell; when you must shell, write PowerShell-safe commands (no `&&`/`<`/`>`/inline-jq; commit via `-F`; `ConvertFrom-Json` for `gh`).
- **Safety gate before building:** if a task needs hardware/access you don't have (GPU, Olares), say so and do the safe subset. **Never fabricate a passing smoke test.**
- **Plan in dependency order**, keep a TODO list for multi-step work, and finish what you start.
- **Self-review before presenting:** run all gates, verify live, and summarize what you verified and how.
- **Governance is non-negotiable:** keep `api/app/domain/` framework-free (ports & adapters; repositories `flush`, routes `commit`); config only via `aimpos-config` (no `os.getenv`); all web backend calls through `web/src/api/client.ts`. Record every non-trivial decision as an append-only `D-XX` in `DECISIONS.md` and update `Sprint0_Status.md`/a new `Sprint1_Status.md` tracker.
- **No secrets in commits.** Scan added files; `.env` is gitignored — keep it that way. Never weaken auth or print tokens.
- **Git safety:** never force-push or rewrite shared history; **do not push or open PRs unless the human explicitly asks** (in Sprint 0 the human explicitly approved each push). Commit locally and propose.
- **Communicate plainly.** Lead with the result, note what's verified vs assumed, and surface blockers early (especially the GPU/Olares gate).

---

## 6. Workflow & Definition of Done

**Per issue:** create a `feature/<task-id>-<slug>` branch → implement → run all local gates → live-verify → write `DECISIONS.md` (`D-XX`) + tracker update → open a PR (only when asked) → **rebase-merge** → delete branch → close the issue referencing the PR.

**Definition of Done** (see `docs/governance/definition-of-done.md`): code + tests pass, ruff/format/mypy clean, live-verified, decision recorded, docs/runbook updated, no secrets, scope held.

**Sprint 1 exit gates (SCR-2026-001 / D-31):**

- **S1-SW (software exit):** 9-service compose valid; CI; smoke scripts + runbooks authored; hermetic postgres/minio smokes pass; decisions recorded. **Unblocks Sprint 2** (Temporal workflow, US-07).
- **M1-DV (deployment validation):** Ollama + ComfyUI smoke pass on Olares (or failure protocol on US-06); zero-egress verified; US-02/US-06/EPIC-01/FEAT-INFRA closable. **Blocks Sprint 3**, not Sprint 2.

Historical wording in `Sprint 0 — Platform Skeleton.md` §7 is superseded for execution — see that doc §12 (append-only).

---

## 7. First-session checklist

1. Bring up today's stack; confirm `/health` is 200 and the SPA loads (sanity that nothing regressed).
2. Read this doc + `sprint-0-briefing.md` + recent `DECISIONS.md`.
3. **Add CI** (`.github/workflows/ci-api.yml` + web job) — resolves TD-21 and gates everything after.
4. Knock out pure-software items (#62 GPU sequencing docs, #69/#70/#71 tech-debt) behind CI.
5. Author the full compose (#44); validate with `docker compose config`.
6. **Confirm GPU + Olares access.** If yes: complete **M1-DV** (#47/#60/#61/#49/#48, live validation, close US-06/US-02/EPIC-01). If no: finish **S1-SW**, document M1-DV blocker, do not fabricate smokes; Sprint 2 may proceed after S1-SW per D-31.

---

## 8. Key references

- `sprint-0-briefing.md` — architecture, repo map, decisions, gotchas (the "what exists" companion to this doc).
- `Sprint 0 — Platform Skeleton.md` §3.2 (Phase B), §4, §8/§9 — frozen scope, failure protocol, exit gates.
- `Sprint Reclassification.md` — authoritative sprint/class mapping (US-02/US-06 = class B / Sprint 1).
- `docs/governance/` — `coding-standards.md`, `definition-of-done.md`, `development-workflow.md`, `branching-strategy.md`.
- `DECISIONS.md` — D-01…D-28 (append-only).
- `Technology Recommendations.md`, `Workflow Architecture.md`, `Multi-Agent Architecture.md` — for the worker/Temporal/Ollama/ComfyUI design coming in Sprint 1–2.
