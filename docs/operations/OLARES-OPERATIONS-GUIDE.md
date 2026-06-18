# Olares Operations Guide

**Version:** 1.0 (Phase 6.5)  
**Cluster:** `olares@10.0.0.34` · namespace `aimpos-mwayolares`

---

## 1. Deployment model

| Component | Pattern |
|-----------|---------|
| Images | Built on Olares host from synced tarball (`/tmp/aimpos-usvXX-src.tgz`) |
| Tags | Acceptance: `usvXX-phaseY` · Release: manifest semver (`v0.16.0-phase6-episode`) |
| DB | `aimpos-postgres-0` StatefulSet |
| Workflow | Temporal `deploy/temporal` |
| GPU | ComfyUI shared service (STORYBOARD); Ollama (SCRIPT) |
| TTS | espeak (CPU) default; speaches optional on Olares |

---

## 2. Standard deploy sequence

1. `olares_probe.sh` — pre-flight (pods, secrets, GPU services)
2. Apply migration SQL or Alembic (`apply_000X_sql_olares.sh`)
3. `build_usvXX_olares.sh` — docker build api/worker/web
4. `deploy_usvXX.sh` — rollout deployments
5. `olares_probe.sh` — post-flight
6. `verify_usvXX_e2e.sh` — acceptance (single instance, `flock`)
7. Pull evidence to repo `evidence/us-vXX-verification/olares-<date>/`

Orchestrator: `deploy/dev/verify_usvXX_olares.ps1`

---

## 3. Drift prevention controls

### 3.1 Manifest as source of truth (D-71)

All production pins read from `deploy/release/manifest.yaml`:

- Image tags (api, web, worker)
- `database.alembic_head`
- Worker env pins (`COMFYUI_WORKFLOW`, `VIDEO_I2V_ENABLED`, `NARRATION_ENABLED`)

### 3.2 Drift detection

Script: `deploy/k8s/phase3d-verify/check_drift.sh`

Checks:

- Deployment image tags vs `EXPECTED_*_TAG`
- Alembic version vs `EXPECTED_ALEMBIC`

**Gap:** Default `EXPECTED_ALEMBIC=0003` — **must** be set from manifest (currently **0005** for v0.16).

Run via:

```powershell
make check-drift-olares   # if Makefile target exists
# or verify_all_olares.ps1 drift step with env overrides
```

### 3.3 Image drift incidents (history)

| Phase | Incident | Cause | Mitigation |
|-------|----------|-------|------------|
| 3B/3C | API/worker tag mismatch | Ad hoc `:dev` / `:phase3c` | D-71 manifest pins |
| US-V05 | Docker not running on build host | Manual build failure | Orchestrator pre-check |
| US-V07 | Worker idle, zero GPU | E2E finished + VIDEO_I2V disabled | Expected; document in acceptance |

### 3.4 Deployment validation improvements (recommended)

| Control | Status | Action |
|---------|--------|--------|
| Post-deploy drift check | Partial | Pass manifest alembic + tags automatically |
| Single E2E lock | US-V07 only | Propagate to US-V05/06 scripts |
| `cancel_stale_run.sh` | US-V07, US-V14/16 | Standardize in `deploy/k8s/lib/` |
| Probe before/after | `olares_probe.sh` | Required in all orchestrators |
| Evidence auto-fetch | US-V07 orchestrator | Template for future phases |

---

## 4. Health review checklist

| Check | Command / endpoint |
|-------|-------------------|
| API health | `GET /health` via cluster IP |
| Postgres | `psql` alembic_version, active runs count |
| Worker | Temporal task queue processing |
| ComfyUI | shared pod logs; GPU VRAM spike during STORYBOARD |
| Ollama | SCRIPT stage latency |
| Stuck runs | `status IN (AWAITING_APPROVAL)` with no E2E driver |

**Cleanup:** `cancel_stale_run.sh <run_id>` — terminate Temporal + mark CANCELLED.

---

## 5. Verification history on cluster

| Acceptance | Script | Result | Notes |
|------------|--------|--------|-------|
| US-V05 | `verify_usv05_e2e.sh` | PASS | PATH A/B/C |
| US-V06 | `verify_usv06_e2e.sh` | PASS | Manifest v3 |
| US-V07 primary | `verify_usv07_e2e.sh` | FAIL=1 | C1 orphan |
| US-V07 C1 supplement | `verify_path_c1_olares.sh` | PASS | Authoritative C1 |

Evidence archived locally under `evidence/us-v0*-verification/olares-2026-06-17/`.

---

## 6. Operational risks

1. **Concurrent verification** — orphan runs at approval gates
2. **Approve API project-scoping** — wrong run approved if multiple active (mitigated by one-active-run rule)
3. **verify_all_olares stale** — does not validate Phase 4–6 deployments
4. **Acceptance tags ≠ release tags** — cluster may run `usv07-phase6` while manifest says `v0.16.0-phase6-episode` until operator retags
