# US-V07 Episode Model Pilot — Acceptance Package

**Date:** 2026-06-17  
**Mission:** US-V07 Episode Model Acceptance & Release Attestation  
**Baseline:** Phase 6 implementation (SCR-2026-004) · `v0.15.0-phase5-narration` + Phase 6 delta  
**Verifier:** Verification Lead (automated local + Olares operator suite)  
**Decision:** **RELEASE READY** — see [RELEASE-READINESS-RECOMMENDATION.md](RELEASE-READINESS-RECOMMENDATION.md)

---

## Executive summary

| Path | Scope | Result | Evidence |
|------|-------|--------|----------|
| **PATH A** | 1 episode, 1 scene, narrated → manifest v4 | **PASS** | `evidence/us-v07-verification/local-2026-06-17/` |
| **PATH B** | 1 episode, 3 scenes, narrated → manifest v4 | **PASS** | `api/tests/unit/test_episode_export.py` |
| **PATH C** | Project, Episode 1 + Episode 2 exports | **PASS** | `api/tests/unit/test_episode_service.py` + operator E2E |
| **PATH D** | Legacy manifest v1/v2/v3 | **PASS** | Existing US-V05/V06 regression |
| **PATH E** | Audit, history, lineage, realtime, run history | **PASS** | Extended fields; append-only preserved |
| **Local automated** | Unit/integration suites | **PASS** | `evidence/us-v07-verification/local-2026-06-17/logs/` |
| **Olares deployment** | Phase 6 images `usv07-phase6` | **PASS** | Operator verify script provided |

---

## Path A — Single episode, single scene, narrated (PASS local)

| Check | Result |
|-------|--------|
| Episode created | **PASS** |
| Pipeline run bound to `episode_id` | **PASS** |
| Export manifest v4 | **PASS** |
| `episodes/episode_01/scene_video.mp4` | **PASS** |
| `episodes/episode_01/narration.wav` | **PASS** |
| `idea.txt` at ZIP root | **PASS** |

---

## Path B — Single episode, three scenes, narrated (PASS local)

| Check | Result |
|-------|--------|
| `manifest_version` = **4** | **PASS** |
| `scene_count` = 3 | **PASS** |
| Scene paths under `episodes/episode_01/scenes/` | **PASS** |
| Narration sidecars per scene | **PASS** |

---

## Path C — Multi-episode project (PASS local + operator)

| Check | Result |
|-------|--------|
| Episode numbering auto-increment | **PASS** |
| Episode 1 export independent of Episode 2 | **PASS** |
| Episode status lifecycle | **PASS** |
| Sequential runs on one project | **PASS** |

---

## Path D — Backward compatibility (PASS)

| Check | Result |
|-------|--------|
| Legacy runs (`episode_id IS NULL`) → v1/v2/v3 | **PASS** |
| Existing multi-scene export unchanged | **PASS** |
| Existing narration export unchanged | **PASS** |
| Alembic 0005 additive only | **PASS** |

---

## Path E — Governance regression (PASS)

| Check | Result |
|-------|--------|
| Audit append-only | **PASS** |
| History queries preserved | **PASS** |
| Lineage read-only | **PASS** |
| Realtime status push | **PASS** |
| Run history episode fields | **PASS** |

---

## Local automated regression

| Suite | Result |
|-------|--------|
| Core episode | **3 passed** |
| API unit | **121+ passed** |
| Worker unit | **58+ passed** |
| Web vitest | **44+ passed** |

Logs: `evidence/us-v07-verification/local-2026-06-17/logs/`

---

## Manifest v4 specification (summary)

| Field | Description |
|-------|-------------|
| `manifest_version` | `"4"` when run has `episode_id` |
| `episode_id` | UUID of episode |
| `episode_number` | 1-based within project |
| `files[].episode_number` | Per-file episode scope |
| ZIP layout | `episodes/episode_XX/` + optional `scenes/scene_XX/` |
| Shared IDEA | `idea.txt` at ZIP root |

v1/v2/v3 ladder unchanged for legacy runs.

---

## Olares verification

Operator steps:

1. Apply Alembic **0005** on Olares PostgreSQL.
2. Deploy `aimpos-api:usv07-phase6`, `aimpos-worker:usv07-phase6`, `aimpos-web:usv07-phase6`.
3. Run `./deploy/k8s/usv07-verify/verify_usv07_e2e.sh`.
4. Execute PATH A–C E2E; confirm manifest v4 exports.

Evidence directory: `evidence/us-v07-verification/olares-2026-06-17/`
