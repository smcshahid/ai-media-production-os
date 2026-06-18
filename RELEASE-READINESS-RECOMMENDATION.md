# Release Readiness Recommendation — Phase 6 Episode Model Pilot

**Date:** 2026-06-18  
**Release:** `v0.16.0-phase6-episode`  
**Baseline:** `v0.15.0-phase5-narration`  
**SCR:** SCR-2026-004 (ACCEPTED)  
**Acceptance:** US-V07 **ACCEPTED**

---

## Recommendation

**RELEASE READY** — Olares attestation complete (PATH A–E PASS with C1 supplemental). Authorized for annotated tag **`v0.16.0-phase6-episode`**.

---

## Final PASS/FAIL matrix

| Path | Scope | Olares | Final |
|------|-------|--------|-------|
| **PATH A** | 1 episode, 1 scene, narrated → manifest v4 | PASS | **PASS** |
| **PATH B** | 1 episode, 3 scenes, narrated → manifest v4 | PASS | **PASS** |
| **PATH C1** | Multi-episode — Episode 1 export | FAIL (primary) / PASS (supplement) | **PASS** |
| **PATH C2** | Multi-episode — Episode 2 export | PASS | **PASS** |
| **PATH D** | Legacy manifest v1/v2/v3 | PASS | **PASS** |
| **PATH E** | Audit, history, lineage, run history | PASS | **PASS** |
| **Local automated** | Core + API + worker + web | PASS | **PASS** |

Matrix detail: `evidence/us-v07-verification/olares-2026-06-17/PASS-FAIL-MATRIX.md`

---

## Manifest v4

Episode-scoped exports use `manifest_version=4` with:

- Top-level `episode_id`, `episode_number`
- ZIP paths under `episodes/episode_XX/`
- Shared `idea.txt` at ZIP root
- Narration sidecars preserved (v3 semantics within v4 layout)

Legacy runs without `episode_id` continue v1/v2/v3 ladder unchanged.

---

## Migration notes

1. Run `alembic upgrade head` (revision **0005**).
2. No data migration required.
3. Existing projects continue without episodes until `POST /episodes` is used.

---

## Deployment checklist

| Step | Status |
|------|--------|
| Apply Alembic 0005 on PostgreSQL | **DONE** (Olares) |
| Deploy API / worker / web `usv07-phase6` | **DONE** (Olares) |
| Run `deploy/dev/verify_phase6_local.ps1` | **PASS** |
| Run `deploy/k8s/usv07-verify/verify_usv07_e2e.sh` | **PASS** (C1 supplement) |
| Archive evidence | **DONE** |

---

## Defects

| Severity | Open | Notes |
|----------|------|-------|
| S1 | 0 | — |
| S2 | 0 | — |
| S3 | 0 | C1 orphan closed via supplement + script hardening |

---

## Risks for operators

1. Export integrators must handle manifest v4 episode paths.
2. One active pipeline run per project (episode or legacy).
3. Do not run multiple E2E verification instances concurrently on one project.

---

## Phase 7 guidance

**Recommended:** Platform maturity (`verify-all` adoption, operational runbooks) before character bible or publishing SCRs. Character bible remains out of scope until governance authorizes a new SCR.
