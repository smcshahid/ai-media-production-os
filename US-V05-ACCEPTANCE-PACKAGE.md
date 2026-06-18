# US-V05 Multi-Scene Pilot — Acceptance Package

**Date:** 2026-06-17  
**Mission:** US-V05 Multi-Scene Acceptance & Release Attestation  
**Baseline:** Phase 4 implementation (SCR-2026-002) · `v0.13.0-phase3d` + Phase 4 delta  
**Verifier:** Verification Lead (automated + Olares SSH)  
**Decision:** **RELEASE READY** — see [RELEASE-READINESS-RECOMMENDATION.md](RELEASE-READINESS-RECOMMENDATION.md)

---

## Executive summary

| Path | Scope | Result | Evidence |
|------|-------|--------|----------|
| **PATH A** | 2-scene Olares E2E → manifest v2 | **PASS** | `evidence/.../olares-2026-06-17/path-a/` |
| **PATH B** | 3-scene Olares E2E → manifest v2 | **PASS** | `evidence/.../olares-2026-06-17/path-b/` |
| **PATH C** | Single-scene backward compatibility on Olares | **PASS** | `evidence/.../olares-2026-06-17/path-c/` |
| **Local automated** | Unit/integration suites | **PASS** | `evidence/.../local-2026-06-17/logs/` |
| **Olares migration** | Alembic 0004 | **PASS** | `evidence/.../logs/migration-0004.log` |
| **Olares deployment** | Phase 4 images `usv05-phase4` | **PASS** | api / worker / web rolled 2026-06-17 |

**Commit, tag, and push** may proceed when release owner authorizes (all mission gates satisfied).

---

## Path A — Two-scene project (PASS on Olares)

**Run:** `99e70e94-89f0-4cf9-b5e5-719108862d1b`  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`  
**Flow:** Idea → Story → Script → Scene1 Storyboard → Scene1 Video → Scene2 Storyboard → Scene2 Video → COMPLETED

| Check | Result | Evidence |
|-------|--------|----------|
| Pipeline COMPLETED | **PASS** | `logs/e2e-olares.log` |
| Export manifest v2 | **PASS** (`scene_count=2`) | `path-a/path-A-export.zip` (26.8 MB) |
| Audit (run filter) | **PASS** | `path-a/path-A-audit.json` |
| Asset history (run filter) | **PASS** | `path-a/path-A-history.json` |
| Lineage | **PASS** | `path-a/path-A-lineage.json` |

**Manifest excerpt:**

```json
{
  "manifest_version": "2",
  "scene_count": 2,
  "pipeline_run_id": "99e70e94-89f0-4cf9-b5e5-719108862d1b"
}
```

---

## Path B — Three-scene project (PASS on Olares)

**Run:** `f8d89b35-f333-474c-a012-d3ab1d5864b3`  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`  
**Wall-clock:** ~10 minutes (STORYBOARD + VIDEO stages per scene)

| Check | Result | Evidence |
|-------|--------|----------|
| Pipeline COMPLETED | **PASS** | `logs/e2e-olares.log` |
| Export manifest v2 | **PASS** (`scene_count=3`) | `path-b/path-B-export.zip` (41.3 MB) |
| Audit (run filter) | **PASS** | `path-b/path-B-audit.json` |
| Asset history (run filter) | **PASS** | `path-b/path-B-history.json` |
| Lineage | **PASS** | `path-b/path-B-lineage.json` |

**Manifest excerpt:**

```json
{
  "manifest_version": "2",
  "scene_count": 3,
  "pipeline_run_id": "f8d89b35-f333-474c-a012-d3ab1d5864b3"
}
```

---

## Path C — Backward compatibility (PASS on Olares)

**Legacy run:** `e5da4992-226c-4969-b95d-e7a2c6415b30` (COMPLETED, pre–multi-scene, `scene_count` NULL)  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`  
**Attestation window:** Verified **before** PATH A/B multi-scene runs on the acceptance project (preserves v1 export contract).

| Check | HTTP | Result | Evidence |
|-------|------|--------|----------|
| Export legacy run | 200 | **PASS** manifest v1 | `path-c/legacy-export.zip` |
| Asset history (project) | 200 | **PASS** | `path-c/history.json` |
| Asset history (run filter) | 200 | **PASS** | `path-c/history-run.json` |
| Audit (project) | 200 | **PASS** | `path-c/audit.json` |
| Audit (run filter) | 200 | **PASS** | `path-c/audit-run.json` |
| Lineage | 200 | **PASS** | `path-c/lineage.json` |
| Run history | 200 | **PASS** | `path-c/runs.json` |
| Pipeline status | 200 | **PASS** | `path-c/status.json` |
| `scene_count=1` start probe | 201 | **PASS** | `path-c/start-scene-count-probe.json` |

**Note:** Re-exporting legacy runs on a project **after** multi-scene assets are present may yield manifest v2 (shared project asset model). Backward compatibility is attested on the pre–multi-scene export snapshot above.

---

## Migration evidence (Olares PASS)

| Step | Before | After |
|------|--------|-------|
| `alembic_version` | `0003` | `0004` |
| `pipeline_runs.scene_count` | absent | present |
| `pipeline_runs.current_scene_index` | absent | present |
| `approvals.scene_index` | absent | present |

**Script:** `deploy/k8s/usv05-verify/apply_0004_sql_olares.sh`

---

## Regression evidence (local automated PASS)

| Suite | Result | Log |
|-------|--------|-----|
| API unit tests | **115 passed** | `evidence/.../local-2026-06-17/logs/pytest-api.txt` |
| Worker unit tests | **56 passed** | `evidence/.../local-2026-06-17/logs/pytest-worker.txt` |
| Web vitest | **43 passed** | `evidence/.../local-2026-06-17/logs/vitest-web.txt` |

---

## Olares cluster state (post-acceptance)

| Deployment | Image | Phase 4? |
|------------|-------|----------|
| aimpos-api | `aimpos-api:usv05-phase4` | **Yes** |
| aimpos-worker | `aimpos-worker:usv05-phase4` | **Yes** |
| aimpos-web | `aimpos-web:usv05-phase4` | **Yes** |
| DB alembic | **0004** | **Yes** |

---

## Governance validation matrix

| Capability | Local tests | Olares live | Result |
|------------|-------------|-------------|--------|
| Audit | PASS | PASS (A/B/C) | **PASS** |
| History | PASS | PASS (A/B/C) | **PASS** |
| Diff | PASS (vitest) | Not browser-tested | **PASS** (automated) |
| Lineage | PASS | PASS (A/B/C) | **PASS** |
| Run history | PASS | PASS (A/B/C) | **PASS** |
| Export manifest v1 | PASS | PASS (Path C) | **PASS** |
| Export manifest v2 | PASS (unit) | PASS (Path A/B) | **PASS** |
| 2-scene workflow | Unit + Olares E2E | PASS | **PASS** |
| 3-scene workflow | Unit + Olares E2E | PASS | **PASS** |
| Scene navigation UI | PASS (vitest/build) | Not browser-tested | **PASS** (automated) |

---

## Defects (closed)

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| USV05-D01 | SEV-1 | Phase 4 container images not deployed to Olares | **CLOSED** |
| USV05-D02 | SEV-1 | PATH A Olares E2E not completed | **CLOSED** |
| USV05-D03 | SEV-1 | PATH B Olares E2E not completed | **CLOSED** |
| USV05-D04 | SEV-2 | Docker daemon unavailable | **CLOSED** |
| USV05-D05 | SEV-2 | Manifest v2 not attested on Olares | **CLOSED** |

**Verification script fixes (non-product):** `poll_until COMPLETED` stage check and `/lineage/{run_id}` URL corrected in `deploy/k8s/usv05-verify/verify_usv05_e2e.sh`.

---

## PASS/FAIL summary

| Gate | Result |
|------|--------|
| PATH A | **PASS** |
| PATH B | **PASS** |
| PATH C | **PASS** |
| Olares migration 0004 | **PASS** |
| Olares Phase 4 deploy | **PASS** |
| Local automated regression | **PASS** |
| **Overall release attestation** | **PASS** |

---

## Related documents

- [US-V05-CLOSURE-REPORT.md](US-V05-CLOSURE-REPORT.md)
- [RELEASE-READINESS-RECOMMENDATION.md](RELEASE-READINESS-RECOMMENDATION.md)
- [PHASE-4-MULTI-SCENE-CLOSURE.md](PHASE-4-MULTI-SCENE-CLOSURE.md)
